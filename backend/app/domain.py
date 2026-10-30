import hashlib
import re
from typing import Protocol


class Embeddings(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorIndex(Protocol):
    def upsert(self, tenant: str, records: list[dict]) -> None: ...
    def query(self, tenant: str, kb: str, vector: list[float], top_k: int) -> list[str]: ...
    def delete(self, tenant: str, document: str) -> None: ...


def chunks(document_id: str, version: int, pages: list[tuple[int | None, str]]):
    result = []
    for page, text in pages:
        text = re.sub(r"\s+", " ", text).strip()
        for offset in range(0, len(text), 1000):
            part = text[offset : offset + 1200]
            if not part:
                continue
            key = hashlib.sha256(f"{document_id}:{version}:{page}:{offset}".encode()).hexdigest()
            result.append({"id": key, "text": part, "page": page})
    return result


def terms(text: str):
    return set(re.findall(r"\b\w{3,}\b", text.lower())) - {
        "the",
        "and",
        "what",
        "does",
        "with",
        "that",
        "this",
        "are",
        "for",
    }
