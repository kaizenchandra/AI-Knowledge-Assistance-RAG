import os
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from test_integration import context as context
from test_integration import pytestmark as pytestmark
from test_integration import resources, upload_ready

from app import worker
from app.db import Document, Job, Session
from app.history import current_history
from app.scanning import MalwareDetected


def queued(client, kb):
    result = client.post(
        "/api/v1/documents",
        params={"kb_id": kb},
        files={"file": ("quarantine.txt", b"Synthetic scanner fixture", "text/plain")},
    )
    assert result.status_code == 202
    doc = result.json()["id"]
    with Session() as db:
        job = db.scalar(select(Job.id).where(Job.document_id == doc))
    return doc, job


def test_malware_is_quarantined_without_parsing(context, monkeypatch):
    client, _ = context
    _, kb = resources(client)
    doc, job = queued(client, kb)

    def reject(data):
        raise MalwareDetected("Synthetic detection")

    monkeypatch.setattr(worker, "scan", reject)
    monkeypatch.setattr(
        worker, "parse_isolated", lambda *args: pytest.fail("Quarantined data reached parser")
    )
    worker.work_once(job)
    with Session() as db:
        assert db.get(Document, doc).status == "quarantined"
        assert db.get(Job, job).state == "quarantined"


def test_stale_job_schedules_generation_cleanup(context):
    client, _ = context
    _, kb = resources(client)
    doc, job = queued(client, kb)
    with Session.begin() as db:
        db.get(Document, doc).version = 2
    worker.work_once(job)
    with Session() as db:
        assert db.get(Job, job).state == "obsolete"
        purge = db.scalar(select(Job).where(Job.document_id == doc, Job.kind == "purge_version"))
        assert purge.version == 1


def test_deleted_evidence_removed_from_model_history(context):
    client, actors = context
    _, kb = resources(client)
    doc, _ = upload_ready(client, kb)
    message = SimpleNamespace(
        role="assistant", text="Sensitive previous answer", citations=[{"document_id": doc, "version": 1}]
    )
    with Session() as db:
        assert current_history(db, actors[0], [message])
    assert client.delete("/api/v1/documents/" + doc).status_code == 204
    with Session() as db:
        assert current_history(db, actors[0], [message]) == []


@pytest.mark.skipif(os.getenv("RUN_SCANNER_TESTS") != "1", reason="Requires real scanner")
def test_real_scanner_quarantines_upload(context):
    client, _ = context
    _, kb = resources(client)
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    response = client.post(
        "/api/v1/documents", params={"kb_id": kb}, files={"file": ("scanner-test.txt", eicar, "text/plain")}
    )
    assert response.status_code == 202
    document = response.json()["id"]
    with Session() as db:
        job = db.scalar(select(Job.id).where(Job.document_id == document))
    worker.work_once(job)
    with Session() as db:
        assert db.get(Document, document).status == "quarantined"
        assert db.get(Job, job).state == "quarantined"
    assert client.delete("/api/v1/documents/" + document).status_code == 204
    with Session() as db:
        cleanup = db.scalar(select(Job.id).where(Job.document_id == document, Job.kind == "delete"))
    worker.work_once(cleanup)


def test_late_upsert_after_lost_lease_and_delete_still_queues_cleanup(context, monkeypatch):
    client, _ = context
    _, kb = resources(client)
    document, job = queued(client, kb)

    class Index:
        def validate(self):
            pass

        def upsert(self, tenant, records):
            with Session.begin() as db:
                db.get(Document, document).deleted = True
                db.get(Job, job).lease = "new-owner"

        def visible(self, *args):
            return True

    monkeypatch.setattr(worker, "settings", lambda: SimpleNamespace(provider="live", embedding_model="test"))
    monkeypatch.setattr(worker, "scan", lambda data: None)
    monkeypatch.setattr(worker, "vector_index", lambda: Index())
    monkeypatch.setattr(
        worker, "embeddings", lambda: SimpleNamespace(embed=lambda texts: [[1.0] for _ in texts])
    )
    worker.work_once(job)
    with Session() as db:
        assert db.get(Document, document).status != "ready"
        assert (
            db.scalar(select(Job).where(Job.document_id == document, Job.kind == "purge_version")).version
            == 1
        )
