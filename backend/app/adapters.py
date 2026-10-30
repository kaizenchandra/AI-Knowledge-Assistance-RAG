import pathlib
from functools import lru_cache

import boto3
from botocore.config import Config
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pinecone import Pinecone

from .config import settings


class Storage:
    def __init__(self):
        self.cfg = settings()
        self.client = (
            boto3.client(
                "s3",
                region_name=self.cfg.aws_region,
                endpoint_url=self.cfg.s3_endpoint_url or None,
                config=Config(
                    connect_timeout=5, read_timeout=20, retries={"mode": "standard", "total_max_attempts": 3}
                ),
            )
            if self.cfg.storage == "s3"
            else None
        )

    def path(self, key):
        root = pathlib.Path(self.cfg.storage_path).resolve()
        path = (root / key).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Invalid object key")
        return path

    def put(self, key, data):
        if self.client:
            self.client.put_object(
                Bucket=self.cfg.s3_bucket, Key=key, Body=data, ServerSideEncryption="AES256"
            )
        else:
            path = self.path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def get(self, key):
        if self.client:
            body = self.client.get_object(Bucket=self.cfg.s3_bucket, Key=key)["Body"]
            try:
                return body.read(self.cfg.max_upload_bytes + 1)
            finally:
                body.close()
        return self.path(key).read_bytes()

    def delete(self, key):
        if self.client:
            self.client.delete_object(Bucket=self.cfg.s3_bucket, Key=key)
        else:
            self.path(key).unlink(missing_ok=True)


def parse(filename: str, data: bytes):
    from .parsing import extract

    return extract(filename, data, settings().max_upload_bytes, settings().max_text_chars)


class LiveEmbeddings:
    def __init__(self):
        cfg = settings()
        self.client = OpenAIEmbeddings(
            model=cfg.embedding_model,
            dimensions=cfg.embedding_dimensions,
            api_key=cfg.openai_api_key,
            request_timeout=20,
            max_retries=2,
        )

    def embed(self, texts):
        return self.client.embed_documents(texts)


class PineconeIndex:
    def __init__(self):
        cfg = settings()
        self.client = Pinecone(api_key=cfg.pinecone_api_key, timeout=10)
        self.index = self.client.Index(host=cfg.pinecone_host)

    def upsert(self, tenant, records):
        for start in range(0, len(records), 50):
            self.index.upsert(namespace=tenant, vectors=records[start : start + 50], timeout=20)

    def query(self, tenant, kb, vector, top_k=12):
        response = self.index.query(
            namespace=tenant,
            vector=vector,
            top_k=top_k,
            filter={"kb_id": {"$eq": kb}, "embedding_version": {"$eq": embedding_version()}},
            include_metadata=False,
            timeout=15,
        )
        return [match.id for match in response.matches]

    def delete(self, tenant, document):
        self.index.delete(namespace=tenant, filter={"document_id": {"$eq": document}}, timeout=20)

    def delete_version(self, tenant, document, version):
        self.index.delete(
            namespace=tenant,
            filter={"document_id": {"$eq": document}, "version": {"$eq": version}},
            timeout=20,
        )

    def validate(self):
        cfg = settings()
        description = self.client.describe_index(cfg.pinecone_index)
        if description.host.removeprefix("https://").rstrip("/") != cfg.pinecone_host.removeprefix(
            "https://"
        ).rstrip("/"):
            raise ValueError("Pinecone index host mismatch")
        if description.dimension != cfg.embedding_dimensions or description.metric != "cosine":
            raise ValueError("Pinecone embedding dimension or metric mismatch")
        if not description.status["ready"]:
            raise ValueError("Pinecone index is not ready")

    def visible(self, tenant, kb, records):
        # Probe each vector through the same query path used by retrieval.
        for record in records:
            response = self.index.query(
                namespace=tenant,
                vector=record["values"],
                top_k=1,
                filter={
                    "kb_id": {"$eq": kb},
                    "chunk_id": {"$eq": record["id"]},
                    "embedding_version": {"$eq": embedding_version()},
                },
                timeout=10,
            )
            if record["id"] not in [match.id for match in response.matches]:
                return False
        return True


@lru_cache
def vector_index():
    return PineconeIndex()


@lru_cache
def embeddings():
    return LiveEmbeddings()


def chat_model():
    cfg = settings()
    return ChatOpenAI(
        model=cfg.chat_model,
        api_key=cfg.openai_api_key,
        timeout=25,
        max_retries=1,
        max_tokens=1200,
        stream_usage=True,
    )


def embedding_version():
    import hashlib

    cfg = settings()
    return hashlib.sha256(f"{cfg.embedding_model}:{cfg.embedding_dimensions}".encode()).hexdigest()[:20]
