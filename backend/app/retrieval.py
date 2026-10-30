from sqlalchemy import select

from .adapters import embeddings, vector_index
from .config import settings
from .db import Chunk, Document, KnowledgeBase, Session
from .domain import terms
from .security import Actor, owned


def retrieve(actor: Actor, kb_id: str, question: str):
    with Session() as db:
        owned(db, KnowledgeBase, kb_id, actor)
        stmt = (
            select(Chunk, Document)
            .join(Document)
            .where(
                Document.tenant_id == actor.tenant_id,
                Document.kb_id == kb_id,
                Document.deleted.is_(False),
                Document.status == "ready",
                Chunk.version == Document.version,
            )
        )
        if settings().provider == "live":
            ids = vector_index().query(actor.tenant_id, kb_id, embeddings().embed([question])[0])
            if not ids:
                return []
            rows = list(db.execute(stmt.where(Chunk.id.in_(ids))))
            rows.sort(key=lambda row: ids.index(row[0].id))
        else:
            # Explicit offline baseline: lexical overlap, never presented as semantic retrieval.
            rows = list(db.execute(stmt.limit(5000)))
            query_terms = terms(question)
            rows = [r for r in rows if terms(r[0].text) & query_terms]
            rows.sort(key=lambda r: len(terms(r[0].text) & query_terms), reverse=True)
        result, size = [], 0
        for chunk, doc in rows[:6]:
            if size + len(chunk.text) > settings().max_context_chars:
                break
            size += len(chunk.text)
            result.append(
                {
                    "id": chunk.id,
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "version": doc.version,
                    "page": chunk.page,
                    "text": chunk.text,
                }
            )
        return result
