import asyncio
import hashlib
import json
import logging
import pathlib
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session as DBSession

from .adapters import Storage
from .body_limit import BodyLimitMiddleware
from .config import settings
from .db import (
    Access,
    Approval,
    Chunk,
    Conversation,
    Document,
    Event,
    Feedback,
    Job,
    KnowledgeBase,
    Member,
    Message,
    Session,
    Workspace,
    engine,
    session,
    uid,
)
from .graphs import chat_graph, checkpoint_url, invoke_approval
from .history import current_history
from .preflight import check_live_dependencies
from .security import Actor, actor, owned, require_write, workspace

log = logging.getLogger("rag")
cfg = settings()
cache = Redis.from_url(cfg.redis_url, socket_timeout=2, socket_connect_timeout=2)


@asynccontextmanager
async def lifespan(app):
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url()) as saver:
        app.state.saver = saver
        yield


app = FastAPI(title="Knowledge Intelligence", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cfg.cors_origin],
    allow_methods=["GET", "POST", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)
app.add_middleware(BodyLimitMiddleware, max_upload_bytes=cfg.max_upload_bytes, timeout=cfg.upload_timeout)


@app.middleware("http")
async def request_id(request, call_next):
    request.state.request_id = uid()
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    log.info(
        json.dumps(
            {
                "request_id": request.state.request_id,
                "method": request.method,
                "status": response.status_code,
                "elapsed_ms": round((time.monotonic() - start) * 1000),
            }
        )
    )
    return response


def limited(a: Actor = Depends(actor)):
    # Atomic increment+expiry; Redis failure fails closed instead of removing limits.
    try:
        count = cache.eval(
            "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",
            1,
            "rate:" + a.tenant_id + ":" + a.subject,
        )
    except Exception:
        raise HTTPException(503, "Rate limiter unavailable") from None
    if count > 180:
        raise HTTPException(429, "Request limit exceeded", headers={"Retry-After": "60"})
    return a


def event(db, a, kind, resource_id):
    db.add(Event(tenant_id=a.tenant_id, subject=a.subject, kind=kind, resource_id=resource_id))


def public(row, fields):
    return {key: getattr(row, key) for key in fields.split()}


class Name(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class KBInput(Name):
    workspace_id: str


class ChatInput(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class ConversationInput(BaseModel):
    kb_id: str


class ApprovalInput(BaseModel):
    document_id: str


class Decision(BaseModel):
    approve: bool


class Vote(BaseModel):
    message_id: str
    score: Literal[-1, 1]
    comment: str = Field(default="", max_length=1000)


class MembershipInput(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    role: Literal["viewer", "editor", "admin"]
    workspace_ids: list[str] = Field(default_factory=list, max_length=100)


@app.get("/api/v1/memberships")
def list_members(a: Actor = Depends(limited), db: DBSession = Depends(session)):
    if a.role != "admin":
        raise HTTPException(403, "Administrator required")
    return [
        public(row, "id subject role")
        for row in db.scalars(select(Member).where(Member.tenant_id == a.tenant_id).limit(100))
    ]


@app.post("/api/v1/memberships")
def grant_membership(body: MembershipInput, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    if a.role != "admin":
        raise HTTPException(403, "Administrator required")
    if body.subject == a.subject and body.role != "admin":
        raise HTTPException(409, "Cannot remove your own administrator role")
    for workspace_id in body.workspace_ids:
        workspace(db, a, workspace_id)
    row = db.scalar(select(Member).where(Member.tenant_id == a.tenant_id, Member.subject == body.subject))
    if not row:
        row = Member(tenant_id=a.tenant_id, subject=body.subject, role=body.role)
        db.add(row)
    row.role = body.role
    tenant_workspaces = select(Workspace.id).where(Workspace.tenant_id == a.tenant_id)
    db.execute(
        delete(Access).where(Access.subject == body.subject, Access.workspace_id.in_(tenant_workspaces))
    )
    for workspace_id in set(body.workspace_ids):
        db.add(Access(subject=body.subject, workspace_id=workspace_id))
    db.flush()
    event(db, a, "membership.updated", row.id)
    db.commit()
    return public(row, "id subject role")


@app.delete("/api/v1/memberships/{member_id}", status_code=204)
def revoke_membership(member_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    if a.role != "admin":
        raise HTTPException(403, "Administrator required")
    member = db.scalar(select(Member).where(Member.id == member_id, Member.tenant_id == a.tenant_id))
    if not member:
        raise HTTPException(404, "Member not found")
    if member.subject == a.subject:
        raise HTTPException(409, "Cannot revoke your own membership")
    tenant_workspaces = select(Workspace.id).where(Workspace.tenant_id == a.tenant_id)
    db.execute(
        delete(Access).where(Access.subject == member.subject, Access.workspace_id.in_(tenant_workspaces))
    )
    event(db, a, "membership.revoked", member.id)
    db.delete(member)
    db.commit()


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        cache.ping()
        dependencies = check_live_dependencies()
        if any(value.startswith("unavailable") for value in dependencies.values()):
            raise RuntimeError("External dependency unavailable")
    except Exception:
        raise HTTPException(503, "Dependency unavailable") from None
    return {"status": "ok", "provider": cfg.provider, "dependencies": dependencies}


@app.get("/api/v1/session")
def get_session(a: Actor = Depends(limited)):
    return {**asdict(a), "provider": cfg.provider, "environment": cfg.environment}


@app.get("/api/v1/workspaces")
def workspaces(a: Actor = Depends(limited), db: DBSession = Depends(session)):
    stmt = select(Workspace).where(Workspace.tenant_id == a.tenant_id)
    if a.role != "admin":
        stmt = stmt.join(Access).where(Access.subject == a.subject)
    return [public(r, "id name") for r in db.scalars(stmt.limit(100))]


@app.post("/api/v1/workspaces", status_code=201)
def create_workspace(body: Name, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    if a.role != "admin":
        raise HTTPException(403, "Administrator required")
    row = Workspace(tenant_id=a.tenant_id, name=body.name)
    db.add(row)
    db.flush()
    event(db, a, "workspace.created", row.id)
    db.commit()
    return public(row, "id name")


@app.get("/api/v1/knowledge-bases")
def knowledge_bases(workspace_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    workspace(db, a, workspace_id)
    return [
        public(r, "id name workspace_id")
        for r in db.scalars(
            select(KnowledgeBase)
            .where(KnowledgeBase.tenant_id == a.tenant_id, KnowledgeBase.workspace_id == workspace_id)
            .limit(100)
        )
    ]


@app.post("/api/v1/knowledge-bases", status_code=201)
def create_kb(body: KBInput, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    require_write(a)
    workspace(db, a, body.workspace_id)
    row = KnowledgeBase(tenant_id=a.tenant_id, workspace_id=body.workspace_id, name=body.name)
    db.add(row)
    db.commit()
    return public(row, "id name workspace_id")


@app.get("/api/v1/documents")
def documents(kb_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    owned(db, KnowledgeBase, kb_id, a)
    return [
        public(r, "id filename status version error created")
        for r in db.scalars(
            select(Document)
            .where(Document.tenant_id == a.tenant_id, Document.kb_id == kb_id, Document.deleted.is_(False))
            .order_by(Document.created.desc())
            .limit(100)
        )
    ]


@app.post("/api/v1/documents", status_code=202)
def upload(kb_id: str, file: UploadFile, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    require_write(a)
    kb = owned(db, KnowledgeBase, kb_id, a)
    filename = pathlib.PurePath(file.filename or "document.txt").name[:240]
    if pathlib.Path(filename).suffix.lower() not in {".pdf", ".docx", ".txt", ".md", ".html"}:
        raise HTTPException(415, "Supported formats: PDF, DOCX, TXT, Markdown and HTML")
    data = file.file.read(cfg.max_upload_bytes + 1)
    if not data or len(data) > cfg.max_upload_bytes:
        raise HTTPException(413, "File is empty or exceeds 20 MB")
    digest = hashlib.sha256(data).hexdigest()
    duplicate = db.scalar(
        select(Document).where(
            Document.kb_id == kb_id,
            Document.tenant_id == a.tenant_id,
            Document.digest == digest,
            Document.deleted.is_(False),
        )
    )
    if duplicate:
        return public(duplicate, "id filename status version")
    doc_id = uid()
    key = a.tenant_id + "/" + doc_id + "/1"
    Storage().put(key, data)
    row = Document(
        id=doc_id,
        tenant_id=a.tenant_id,
        workspace_id=kb.workspace_id,
        kb_id=kb.id,
        filename=filename,
        key=key,
        digest=digest,
    )
    db.add(row)
    db.flush()
    db.add(Job(document_id=row.id, version=1))
    event(db, a, "document.uploaded", row.id)
    db.commit()
    return public(row, "id filename status version")


@app.delete("/api/v1/documents/{document_id}", status_code=204)
def remove_document(document_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    require_write(a)
    row = owned(db, Document, document_id, a)
    row.deleted, row.status = True, "deleted"
    db.add(Job(document_id=row.id, version=row.version, kind="delete"))
    event(db, a, "document.deleted", row.id)
    db.commit()


@app.get("/api/v1/citations/{chunk_id}")
def citation(chunk_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    chunk = db.get(Chunk, chunk_id)
    if not chunk:
        raise HTTPException(404, "Source not found")
    doc = owned(db, Document, chunk.document_id, a)
    if doc.status != "ready" or doc.version != chunk.version:
        raise HTTPException(404, "Source version unavailable")
    return {**public(chunk, "id text page version"), "filename": doc.filename, "document_id": doc.id}


@app.post("/api/v1/conversations", status_code=201)
def create_conversation(
    body: ConversationInput, a: Actor = Depends(limited), db: DBSession = Depends(session)
):
    kb = owned(db, KnowledgeBase, body.kb_id, a)
    row = Conversation(tenant_id=a.tenant_id, workspace_id=kb.workspace_id, kb_id=kb.id, subject=a.subject)
    db.add(row)
    db.commit()
    return public(row, "id title kb_id")


def conversation(db, conversation_id, a):
    row = owned(db, Conversation, conversation_id, a)
    if row.subject != a.subject:
        raise HTTPException(404, "Conversation not found")
    return row


@app.get("/api/v1/conversations")
def conversations(kb_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    owned(db, KnowledgeBase, kb_id, a)
    return [
        public(r, "id title kb_id")
        for r in db.scalars(
            select(Conversation)
            .where(
                Conversation.tenant_id == a.tenant_id,
                Conversation.subject == a.subject,
                Conversation.kb_id == kb_id,
            )
            .limit(100)
        )
    ]


@app.get("/api/v1/conversations/{conversation_id}/messages")
def messages(conversation_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    conversation(db, conversation_id, a)
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created.desc())
        .limit(100)
    ).all()
    return [public(r, "id role text citations created") for r in reversed(rows)]


@app.patch("/api/v1/conversations/{conversation_id}")
def rename_conversation(
    conversation_id: str, body: Name, a: Actor = Depends(limited), db: DBSession = Depends(session)
):
    row = conversation(db, conversation_id, a)
    row.title = body.name
    db.commit()
    return public(row, "id title kb_id")


@app.delete("/api/v1/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, request: Request, a: Actor = Depends(limited)):
    with Session.begin() as db:
        row = conversation(db, conversation_id, a)
        db.refresh(row, with_for_update=True)
        if row.active_until > time.time():
            raise HTTPException(409, "Stop the active run before deleting this conversation")
        prefix = a.tenant_id + ":chat:" + conversation_id + ":"
        thread_ids = (
            db.execute(
                text("SELECT DISTINCT thread_id FROM checkpoints WHERE starts_with(thread_id, :prefix)"),
                {"prefix": prefix},
            )
            .scalars()
            .all()
        )
        # Keep the row lock until sensitive checkpoint deletion completes.
        for thread_id in thread_ids:
            await request.app.state.saver.adelete_thread(thread_id)
        ids = select(Message.id).where(Message.conversation_id == conversation_id)
        db.execute(delete(Feedback).where(Feedback.message_id.in_(ids)))
        db.execute(delete(Message).where(Message.conversation_id == conversation_id))
        db.delete(row)
        event(db, a, "conversation.deleted", conversation_id)


def sse(event):
    return "data: " + json.dumps(event) + "\n\n"


@app.post("/api/v1/conversations/{conversation_id}/messages")
async def ask(conversation_id: str, body: ChatInput, request: Request, a: Actor = Depends(limited)):
    with Session.begin() as db:
        conv = conversation(db, conversation_id, a)
        db.refresh(conv, with_for_update=True)
        if conv.active_until > time.time():
            raise HTTPException(409, "Conversation already has an active run")
        conv.active_until = time.time() + cfg.run_timeout + 10
        conv.title = body.question[:120]
        history = db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created.desc())
            .limit(6)
        ).all()
        prior = current_history(db, a, reversed(history))
        db.add(Message(conversation_id=conv.id, role="user", text=body.question))
        kb_id = conv.kb_id
    run_id = uid()

    async def stream():
        graph = chat_graph(request.app.state.saver)
        config = {
            "configurable": {"thread_id": a.tenant_id + ":chat:" + conversation_id + ":" + run_id},
            "recursion_limit": 8,
        }
        try:
            async with asyncio.timeout(cfg.run_timeout):
                async for mode, data in graph.astream(
                    {"question": body.question, "kb_id": kb_id, "actor": asdict(a), "history": prior},
                    config,
                    stream_mode=["custom", "updates"],
                ):
                    if await request.is_disconnected():
                        return
                    if mode == "custom":
                        yield sse(data)
                state = await graph.aget_state(config)
                answer, sources = state.values["answer"], state.values.get("citations", [])
                with Session.begin() as db:
                    # Reauthorize before publishing final persisted evidence.
                    conversation(db, conversation_id, a)
                    for source in sources:
                        doc = owned(db, Document, source["document_id"], a)
                        if doc.version != source["version"] or doc.status != "ready":
                            raise ValueError("Source changed during generation")
                    message = Message(
                        conversation_id=conversation_id, role="assistant", text=answer, citations=sources
                    )
                    db.add(message)
                    db.flush()
                    message_id = message.id
                    event(db, a, "chat.completed", message_id)
                yield sse(
                    {
                        "type": "final",
                        "text": answer,
                        "citations": sources,
                        "message_id": message_id,
                        "run_id": run_id,
                    }
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("run_failure run=%s type=%s", run_id, type(exc).__name__)
            yield sse(
                {"type": "error", "message": "Run failed or timed out. Retry the question.", "run_id": run_id}
            )
        finally:
            with Session.begin() as db:
                row = db.get(Conversation, conversation_id)
                if row:
                    row.active_until = 0

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})


@app.post("/api/v1/approvals", status_code=201)
def request_approval(body: ApprovalInput, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    require_write(a)
    doc = owned(db, Document, body.document_id, a)
    row = Approval(
        tenant_id=a.tenant_id, workspace_id=doc.workspace_id, subject=a.subject, document_id=doc.id
    )
    db.add(row)
    db.commit()
    invoke_approval(row.id, a.tenant_id)
    return public(row, "id document_id state expires")


@app.get("/api/v1/approvals")
def approvals(workspace_id: str, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    workspace(db, a, workspace_id)
    return [
        public(r, "id document_id state expires subject")
        for r in db.scalars(
            select(Approval)
            .where(Approval.tenant_id == a.tenant_id, Approval.workspace_id == workspace_id)
            .limit(100)
        )
    ]


@app.post("/api/v1/approvals/{approval_id}/decision")
def decide(approval_id: str, body: Decision, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    if a.role != "admin":
        raise HTTPException(403, "Administrator required")
    row = owned(db, Approval, approval_id, a)
    db.refresh(row, with_for_update=True)
    if row.state in {"completed", "rejected", "expired"}:
        raise HTTPException(409, "Approval already decided")
    if row.expires < time.time():
        row.state = "expired"
        db.commit()
        raise HTTPException(409, "Approval expired")
    target = "approved" if body.approve else "denied"
    if row.state not in {"pending", target}:
        raise HTTPException(409, "Conflicting decision")
    row.state, row.decision_by = target, a.subject
    event(db, a, "approval." + target, row.id)
    db.commit()
    result = invoke_approval(row.id, a.tenant_id, Command(resume=body.approve))
    return {"state": result.get("outcome", "pending")}


@app.post("/api/v1/feedback")
def feedback(body: Vote, a: Actor = Depends(limited), db: DBSession = Depends(session)):
    message = db.get(Message, body.message_id)
    if not message or message.role != "assistant":
        raise HTTPException(404, "Answer not found")
    conversation(db, message.conversation_id, a)
    row = db.scalar(select(Feedback).where(Feedback.message_id == message.id, Feedback.subject == a.subject))
    if not row:
        row = Feedback(message_id=message.id, subject=a.subject, score=body.score)
        db.add(row)
    row.score, row.comment = body.score, body.comment
    db.commit()
    return {"saved": True}


@app.get("/api/v1/analytics")
def analytics(a: Actor = Depends(limited), db: DBSession = Depends(session)):
    if a.role != "admin":
        raise HTTPException(403, "Administrator required")
    statuses = db.execute(
        select(Document.status, func.count())
        .where(Document.tenant_id == a.tenant_id, Document.deleted.is_(False))
        .group_by(Document.status)
    ).all()
    answers = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.tenant_id == a.tenant_id, Event.kind == "chat.completed")
    )
    events = db.scalars(
        select(Event).where(Event.tenant_id == a.tenant_id).order_by(Event.created.desc()).limit(30)
    ).all()
    return {
        "documents": dict(statuses),
        "answers": answers,
        "estimated_cost": None,
        "provider": cfg.provider,
        "events": [public(e, "id kind resource_id created") for e in events],
    }
