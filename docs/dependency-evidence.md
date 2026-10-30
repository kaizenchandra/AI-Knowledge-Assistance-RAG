# Dependency and API evidence

Verified on 2026-10-29. Package versions were queried from the official PyPI JSON and npm registry endpoints; dependencies then resolved and installed successfully in Python 3.12 and Node 24 containers. Full Python resolution is in requirements.lock; npm resolution is in package-lock.json. No claim that latest packages are automatically secure or production-certified.

Official documentation read before adapter implementation:

- https://docs.langchain.com/oss/python/langgraph/interrupts — interrupt(), durable checkpointer, thread_id and Command(resume=...).
- https://docs.pinecone.io/guides/manage-data/target-an-index — Pinecone Index(host=...) targeting.
- https://docs.langchain.com/oss/python/integrations/chat/openai — ChatOpenAI, timeout/retry controls and streaming usage.

Installed API inspection confirmed Pinecone.Index accepts host and AsyncPostgresSaver exposes adelete_thread(thread_id). Approval/recovery and checkpoint deletion were exercised against PostgreSQL. Provider adapters have not been called against paid live accounts.

Principal versions: FastAPI 0.162.0; SQLAlchemy 2.1.6; psycopg 3.3.6; Alembic 1.20.1; LangGraph 1.2.18; PostgreSQL checkpoint adapter 3.2.0; langchain-openai 1.7.3; Pinecone SDK 10.2.0; Next.js 16.4.3; React 19.3.1; TypeScript 7.0.2; TanStack Query 5.105.0; Playwright 1.64.1. Terraform 1.17.0 validated AWS provider 6.71.0 configuration.
