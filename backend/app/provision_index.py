"""Explicit operator command; creates a billable Pinecone index only when run."""

import time

from pinecone import Pinecone, ServerlessSpec

from .config import settings


def main():
    cfg = settings()
    pc = Pinecone(api_key=cfg.pinecone_api_key)
    if cfg.pinecone_index not in pc.list_indexes().names():
        pc.create_index(
            name=cfg.pinecone_index,
            dimension=cfg.embedding_dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=cfg.aws_region),
            deletion_protection="enabled",
        )
    deadline = time.monotonic() + 180
    while True:
        index = pc.describe_index(cfg.pinecone_index)
        if index.dimension != cfg.embedding_dimensions or index.metric != "cosine":
            raise ValueError("Existing index has incompatible dimension or metric")
        if index.status["ready"]:
            print("Index ready. Set PINECONE_HOST=" + index.host)
            return
        if time.monotonic() > deadline:
            raise TimeoutError("Index provisioning timed out")
        time.sleep(3)


if __name__ == "__main__":
    main()
