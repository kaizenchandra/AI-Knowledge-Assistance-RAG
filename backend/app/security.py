import secrets
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import Access, Member, Workspace, session


@dataclass(frozen=True)
class Actor:
    subject: str
    tenant_id: str
    role: str


@lru_cache
def jwks():
    return jwt.PyJWKClient(settings().oidc_jwks_url, timeout=5, lifespan=300)


def actor(
    authorization: str = Header(default=""),
    x_tenant_id: str = Header(default=""),
    db: Session = Depends(session),
):
    cfg = settings()
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization[7:]
    if cfg.environment == "development" and cfg.dev_token and secrets.compare_digest(token, cfg.dev_token):
        subject = "dev-admin"
    else:
        try:
            claims = jwt.decode(
                token,
                jwks().get_signing_key_from_jwt(token).key,
                algorithms=["RS256"],
                audience=cfg.oidc_audience,
                issuer=cfg.oidc_issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
            subject = claims["sub"]
        except Exception:
            raise HTTPException(401, "Invalid or expired token") from None
    member = db.scalar(select(Member).where(Member.tenant_id == x_tenant_id, Member.subject == subject))
    if not member:
        raise HTTPException(403, "Tenant membership required")
    return Actor(subject, member.tenant_id, member.role)


def require_write(a: Actor):
    if a.role not in {"editor", "admin"}:
        raise HTTPException(403, "Editor role required")


def workspace(db, a: Actor, workspace_id: str):
    row = db.scalar(select(Workspace).where(Workspace.id == workspace_id, Workspace.tenant_id == a.tenant_id))
    if not row or (
        a.role != "admin"
        and not db.scalar(
            select(Access).where(Access.workspace_id == workspace_id, Access.subject == a.subject)
        )
    ):
        raise HTTPException(404, "Workspace not found")
    return row


def owned(db, model, resource_id: str, a: Actor):
    row = db.scalar(select(model).where(model.id == resource_id, model.tenant_id == a.tenant_id))
    if not row or getattr(row, "deleted", False):
        raise HTTPException(404, "Resource not found")
    workspace(db, a, row.workspace_id)
    return row
