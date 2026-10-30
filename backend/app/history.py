from fastapi import HTTPException

from .db import Document
from .security import owned


def current_history(db, actor, messages):
    """Do not reintroduce revoked, deleted or obsolete evidence via model memory."""
    result = []
    for message in messages:
        if message.role == "assistant":
            valid = True
            for source in message.citations:
                try:
                    doc = owned(db, Document, source["document_id"], actor)
                    if doc.status != "ready" or doc.version != source["version"]:
                        valid = False
                except (HTTPException, KeyError):
                    valid = False
            if not valid:
                continue
        result.append({"role": message.role, "text": message.text[:2000]})
    return result
