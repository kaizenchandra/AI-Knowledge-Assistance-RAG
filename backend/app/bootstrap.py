"""Run migrations first. Seed only explicit development mode."""

from langgraph.checkpoint.postgres import PostgresSaver

from .config import settings
from .db import Member, Session, Tenant
from .graphs import checkpoint_url


def bootstrap():
    with PostgresSaver.from_conn_string(checkpoint_url()) as saver:
        saver.setup()
    if settings().environment == "development":
        with Session.begin() as db:
            if not db.get(Tenant, "local"):
                db.add(Tenant(id="local", name="Local organization"))
                db.flush()
                db.add(Member(tenant_id="local", subject="dev-admin", role="admin"))


if __name__ == "__main__":
    bootstrap()
