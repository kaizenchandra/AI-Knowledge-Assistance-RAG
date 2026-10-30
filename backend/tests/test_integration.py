"""Run only in a disposable Compose database; creates isolated tenant fixtures."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import Chunk, Document, Member, Session, Tenant
from app.main import app, limited
from app.security import Actor
from app.worker import work_once

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1", reason="Requires migrated PostgreSQL and Redis"
)


@pytest.fixture
def context():
    tenant = str(uuid.uuid4())
    subject = "test-" + tenant
    with Session.begin() as db:
        db.add(Tenant(id=tenant, name="Synthetic test organization"))
        db.flush()
        db.add(Member(tenant_id=tenant, subject=subject, role="admin"))
    active = [Actor(subject, tenant, "admin")]
    app.dependency_overrides[limited] = lambda: active[0]
    with TestClient(app) as client:
        yield client, active
    app.dependency_overrides.clear()


def resources(client):
    ws = client.post("/api/v1/workspaces", json={"name": "Test workspace"})
    assert ws.status_code == 201, ws.text
    kb = client.post("/api/v1/knowledge-bases", json={"name": "Policies", "workspace_id": ws.json()["id"]})
    assert kb.status_code == 201, kb.text
    return ws.json()["id"], kb.json()["id"]


def upload_ready(client, kb):
    response = client.post(
        "/api/v1/documents",
        params={"kb_id": kb},
        files={"file": ("policy.txt", b"Employees receive twenty days of vacation annually.", "text/plain")},
    )
    assert response.status_code == 202, response.text
    doc_id = response.json()["id"]
    for _ in range(30):
        work_once()
        with Session() as db:
            if db.get(Document, doc_id).status == "ready":
                break
    with Session() as db:
        assert db.get(Document, doc_id).status == "ready"
        chunk_id = db.scalar(select(Chunk.id).where(Chunk.document_id == doc_id))
    return doc_id, chunk_id


def test_full_flow_and_deleted_source(context):
    client, active = context
    ws, kb = resources(client)
    doc, chunk = upload_ready(client, kb)
    conv = client.post("/api/v1/conversations", json={"kb_id": kb}).json()["id"]
    response = client.post(
        f"/api/v1/conversations/{conv}/messages", json={"question": "How much vacation do employees receive?"}
    )
    assert response.status_code == 200
    assert '"type": "final"' in response.text, response.text
    assert "twenty days" in response.text
    assert client.get("/api/v1/citations/" + chunk).status_code == 200
    history = client.get(f"/api/v1/conversations/{conv}/messages").json()
    assert len(history) == 2
    assert (
        client.post("/api/v1/feedback", json={"message_id": history[-1]["id"], "score": 1}).status_code == 200
    )
    assert client.delete("/api/v1/documents/" + doc).status_code == 204
    assert client.get("/api/v1/citations/" + chunk).status_code == 404
    response = client.post(f"/api/v1/conversations/{conv}/messages", json={"question": "How much vacation?"})
    assert "could not find supporting evidence" in response.text


def test_cross_tenant_and_viewer_denial(context):
    client, active = context
    ws, kb = resources(client)
    doc, chunk = upload_ready(client, kb)
    original = active[0]
    active[0] = Actor("outsider", "other-tenant", "admin")
    assert client.get("/api/v1/documents", params={"kb_id": kb}).status_code == 404
    assert client.get("/api/v1/citations/" + chunk).status_code == 404
    assert client.delete("/api/v1/documents/" + doc).status_code == 404
    active[0] = Actor(original.subject, original.tenant_id, "viewer")
    assert client.post("/api/v1/workspaces", json={"name": "forbidden"}).status_code == 403
    assert client.delete("/api/v1/documents/" + doc).status_code == 403


def test_approval_checkpoint_replay_and_rejection(context):
    client, active = context
    ws, kb = resources(client)
    doc, chunk = upload_ready(client, kb)
    result = client.post("/api/v1/approvals", json={"document_id": doc})
    assert result.status_code == 201, result.text
    approval = result.json()["id"]
    result = client.post(f"/api/v1/approvals/{approval}/decision", json={"approve": True})
    assert result.status_code == 200, result.text
    assert result.json()["state"] == "completed"
    assert client.post(f"/api/v1/approvals/{approval}/decision", json={"approve": True}).status_code == 409
    with Session() as db:
        assert db.get(Document, doc).version == 2
    rejected = client.post("/api/v1/approvals", json={"document_id": doc}).json()["id"]
    assert (
        client.post(f"/api/v1/approvals/{rejected}/decision", json={"approve": False}).json()["state"]
        == "rejected"
    )
    with Session() as db:
        assert db.get(Document, doc).version == 2


def test_auth_required_and_upload_validation(context):
    client, active = context
    ws, kb = resources(client)
    assert (
        client.post(
            "/api/v1/documents", params={"kb_id": kb}, files={"file": ("script.exe", b"bad")}
        ).status_code
        == 415
    )
    app.dependency_overrides.clear()
    assert client.get("/api/v1/session").status_code == 401
