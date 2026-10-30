"""Durable SQL queue: atomic lease, bounded retries, generation fencing."""

import logging
import random
import time

from sqlalchemy import delete, select

from .adapters import Storage, embedding_version, embeddings, vector_index
from .config import settings
from .db import Chunk, Document, Event, Job, Session, uid
from .domain import chunks
from .isolated_parser import parse_isolated
from .scanning import MalwareDetected, scan

log = logging.getLogger(__name__)


def work_once(target_job_id=None):
    now = time.time()
    with Session.begin() as db:
        statement = (
            select(Job)
            .where(Job.available <= now, Job.state.in_(["queued", "processing"]))
            .order_by(Job.available)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if target_job_id:
            statement = statement.where(Job.id == target_job_id)
        job = db.scalar(statement)
        if not job:
            return False
        if job.attempts >= 4:
            job.state = "failed"
            doc = db.get(Document, job.document_id)
            if doc and not doc.deleted and doc.version == job.version:
                doc.status, doc.error = "failed", "Retry limit reached"
            return True
        job.state, job.lease = "processing", uid()
        job.attempts += 1
        job.available = now + 600
        job_id, lease = job.id, job.lease
        doc = db.get(Document, job.document_id)
        if job.kind == "ingest" and (doc.deleted or doc.version != job.version):
            job.state = "obsolete"
            db.add(Job(document_id=doc.id, version=job.version, kind="purge_version"))
            return True
        doc_id, version, tenant, kb, key, filename = (
            doc.id,
            job.version,
            doc.tenant_id,
            doc.kb_id,
            doc.key,
            doc.filename,
        )
        kind = job.kind
        workspace_id = doc.workspace_id
        if kind == "ingest":
            doc.status = "processing"
    try:
        storage = Storage()
        if kind == "purge_version":
            if settings().provider == "live":
                vector_index().delete_version(tenant, doc_id, version)
            with Session.begin() as db:
                current = db.get(Job, job_id)
                if current.lease == lease:
                    current.state = "done"
            return True
        if kind == "delete":
            if settings().provider == "live":
                vector_index().delete(tenant, doc_id)
            storage.delete(key)
            parts = []
        else:
            data = storage.get(key)
            scan(data)
            parts = chunks(doc_id, version, parse_isolated(filename, data))
            if settings().provider == "live":
                vector_index().validate()
                values = embeddings().embed([p["text"] for p in parts])
                records = [
                    {
                        "id": p["id"],
                        "values": v,
                        "metadata": {
                            "document_id": doc_id,
                            "kb_id": kb,
                            "version": version,
                            "embedding_model": settings().embedding_model,
                            "embedding_version": embedding_version(),
                            "chunk_id": p["id"],
                            "tenant_id": tenant,
                            "workspace_id": workspace_id,
                            "filename": filename,
                            "ingestion_version": 1,
                        },
                    }
                    for p, v in zip(parts, values, strict=True)
                ]
                vector_index().upsert(tenant, records)
                deadline = time.monotonic() + 60
                while not vector_index().visible(tenant, kb, records):
                    if time.monotonic() > deadline:
                        raise TimeoutError("Index visibility timeout")
                    time.sleep(2)
        with Session.begin() as db:
            job = db.scalar(select(Job).where(Job.id == job_id).with_for_update())
            doc = db.scalar(select(Document).where(Document.id == doc_id).with_for_update())
            if kind == "ingest" and (doc.deleted or doc.version != version):
                if job.lease == lease:
                    job.state = "obsolete"
                db.add(Job(document_id=doc_id, version=version, kind="purge_version"))
                return True
            if job.lease != lease:
                return True
            db.execute(delete(Chunk).where(Chunk.document_id == doc_id))
            for p in parts:
                db.add(Chunk(id=p["id"], document_id=doc_id, version=version, text=p["text"], page=p["page"]))
            if kind == "ingest":
                doc.status, doc.error = "ready", None
                if version > 1:
                    for old_version in range(1, version):
                        db.add(Job(document_id=doc_id, version=old_version, kind="purge_version"))
            job.state = "done"
            db.add(
                Event(
                    tenant_id=tenant,
                    subject="worker",
                    kind="document." + ("indexed" if kind == "ingest" else "purged"),
                    resource_id=doc_id,
                )
            )
    except MalwareDetected:
        with Session.begin() as db:
            job = db.scalar(select(Job).where(Job.id == job_id).with_for_update())
            doc = db.scalar(select(Document).where(Document.id == doc_id).with_for_update())
            if job.lease == lease:
                job.state = "quarantined"
                if not doc.deleted and doc.version == version:
                    doc.status, doc.error = "quarantined", "Malware detected; source is not searchable"
                db.add(
                    Event(tenant_id=tenant, subject="worker", kind="document.quarantined", resource_id=doc_id)
                )
    except Exception as exc:
        log.warning("ingestion_failure job=%s type=%s", job_id, type(exc).__name__)
        with Session.begin() as db:
            job = db.scalar(select(Job).where(Job.id == job_id).with_for_update())
            if job.lease == lease:
                job.state = "failed" if job.attempts >= 4 else "queued"
                job.available = time.time() + min(60, 2**job.attempts) + random.random()
                doc = db.get(Document, doc_id)
                if not doc.deleted and doc.version == version:
                    doc.status = "failed" if job.state == "failed" else "queued"
                    doc.error = "Processing failed; consult job ID " + job_id
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    while True:
        if not work_once():
            time.sleep(1)
