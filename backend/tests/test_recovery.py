import time

from test_integration import context as context
from test_integration import pytestmark as pytestmark
from test_integration import resources, upload_ready

from app.db import Approval, Document, Session


def test_expired_approval_cannot_change_document(context):
    client, _ = context
    _, kb = resources(client)
    doc, _ = upload_ready(client, kb)
    approval = client.post("/api/v1/approvals", json={"document_id": doc}).json()["id"]
    with Session.begin() as db:
        db.get(Approval, approval).expires = time.time() - 1
    assert client.post(f"/api/v1/approvals/{approval}/decision", json={"approve": True}).status_code == 409
    with Session() as db:
        assert db.get(Document, doc).version == 1


def test_duplicate_upload_and_conversation_erasure(context):
    client, _ = context
    _, kb = resources(client)
    doc, _ = upload_ready(client, kb)
    same = client.post(
        "/api/v1/documents",
        params={"kb_id": kb},
        files={"file": ("again.txt", b"Employees receive twenty days of vacation annually.", "text/plain")},
    )
    assert same.json()["id"] == doc
    conversation = client.post("/api/v1/conversations", json={"kb_id": kb}).json()["id"]
    response = client.post(f"/api/v1/conversations/{conversation}/messages", json={"question": "vacation?"})
    assert '"type": "final"' in response.text
    assert (
        client.patch("/api/v1/conversations/" + conversation, json={"name": "Saved policy"}).status_code
        == 200
    )
    assert client.delete("/api/v1/conversations/" + conversation).status_code == 204
    assert client.get(f"/api/v1/conversations/{conversation}/messages").status_code == 404


def test_membership_management_is_scoped(context):
    client, active = context
    ws, kb = resources(client)
    response = client.post(
        "/api/v1/memberships", json={"subject": "new-member", "role": "viewer", "workspace_ids": [ws]}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "viewer"
    assert client.delete("/api/v1/memberships/" + response.json()["id"]).status_code == 204
    assert (
        client.post(
            "/api/v1/memberships",
            json={"subject": "new-member", "role": "viewer", "workspace_ids": ["wrong-tenant-workspace"]},
        ).status_code
        == 404
    )
