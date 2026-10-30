"""Synthetic retrieval baseline. Never a claim of generative answer quality."""

import json
import time
from pathlib import Path

from sqlalchemy import delete

from .config import settings
from .db import Chunk, Document, KnowledgeBase, Session, Tenant, Workspace, uid
from .domain import chunks
from .retrieval import retrieve
from .security import Actor


def main():
    if settings().provider != "offline":
        raise ValueError(
            "This corpus runner is explicitly offline; live evaluation needs ingestion and provider usage accounting"
        )
    dataset = json.loads((Path(__file__).parent.parent / "evaluation/golden.json").read_text())
    tenant_id, workspace_id, kb_id = uid(), uid(), uid()
    document_ids = []
    mapping = {}
    try:
        with Session.begin() as db:
            db.add(Tenant(id=tenant_id, name="Ephemeral evaluation"))
            db.flush()
            db.add(Workspace(id=workspace_id, tenant_id=tenant_id, name="Evaluation"))
            db.flush()
            db.add(
                KnowledgeBase(id=kb_id, tenant_id=tenant_id, workspace_id=workspace_id, name="Golden corpus")
            )
            db.flush()
            for source in dataset["documents"]:
                doc_id = uid()
                document_ids.append(doc_id)
                mapping[doc_id] = source["key"]
                db.add(
                    Document(
                        id=doc_id,
                        tenant_id=tenant_id,
                        workspace_id=workspace_id,
                        kb_id=kb_id,
                        filename=source["key"] + ".txt",
                        key="evaluation",
                        digest="evaluation",
                        status="ready",
                        version=1,
                    )
                )
                db.flush()
                for part in chunks(doc_id, 1, [(None, source["text"])]):
                    db.add(Chunk(id=part["id"], document_id=doc_id, version=1, text=part["text"]))
        cases = []
        for case in dataset["cases"]:
            start = time.perf_counter()
            rows = retrieve(Actor("evaluation", tenant_id, "admin"), kb_id, case["question"])
            elapsed = (time.perf_counter() - start) * 1000
            predicted = list(dict.fromkeys(mapping[row["document_id"]] for row in rows))
            expected = set(case["expected"])
            hits = len(expected & set(predicted))
            cases.append(
                {
                    "id": case["id"],
                    "predicted": predicted,
                    "expected": case["expected"],
                    "recall": hits / len(expected) if expected else None,
                    "precision": hits / len(predicted) if predicted else None,
                    "abstention_correct": (not predicted) == (not expected),
                    "retrieval_ms": round(elapsed, 3),
                }
            )
        recalls = [c["recall"] for c in cases if c["recall"] is not None]
        print(
            json.dumps(
                {
                    "dataset": dataset["version"],
                    "mode": "offline lexical retrieval",
                    "corpus_documents": len(document_ids),
                    "mean_recall": sum(recalls) / len(recalls),
                    "abstention_accuracy": sum(c["abstention_correct"] for c in cases) / len(cases),
                    "limitations": "Small synthetic corpus; no model, embedding, Pinecone, groundedness, load or production latency measurement.",
                    "cases": cases,
                },
                indent=2,
            )
        )
    finally:
        with Session.begin() as db:
            db.execute(delete(Chunk).where(Chunk.document_id.in_(document_ids)))
            db.execute(delete(Document).where(Document.id.in_(document_ids)))
            db.execute(delete(KnowledgeBase).where(KnowledgeBase.id == kb_id))
            db.execute(delete(Workspace).where(Workspace.id == workspace_id))
            db.execute(delete(Tenant).where(Tenant.id == tenant_id))


if __name__ == "__main__":
    main()
