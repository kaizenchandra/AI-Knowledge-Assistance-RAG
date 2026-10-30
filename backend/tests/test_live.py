"""Explicitly opt-in billable provider checks; no resource provisioning."""

import os
import time
import uuid

import pytest

from app.adapters import Storage, chat_model, embedding_version, embeddings, vector_index
from app.config import settings


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_TESTS") != "1", reason="Live providers require explicit RUN_LIVE_TESTS=1"
)
def test_live_pinecone_embedding_model_roundtrip():
    assert settings().provider == "live", "Configure PROVIDER=live and credentials first"
    index = vector_index()
    index.validate()
    tenant, kb, doc, chunk = ["smoke-" + uuid.uuid4().hex for _ in range(4)]
    vector = embeddings().embed(["The synthetic access code is amber."])[0]
    assert len(vector) == settings().embedding_dimensions
    records = [
        {
            "id": chunk,
            "values": vector,
            "metadata": {
                "document_id": doc,
                "version": 1,
                "kb_id": kb,
                "chunk_id": chunk,
                "embedding_version": embedding_version(),
            },
        }
    ]
    try:
        index.upsert(tenant, records)
        deadline = time.monotonic() + 90
        while not index.visible(tenant, kb, records):
            assert time.monotonic() < deadline, "Freshness deadline exceeded"
            time.sleep(2)
        assert chunk in index.query(tenant, kb, vector)
        assert not index.query(tenant + "-other", kb, vector)
        response = chat_model().invoke([("human", "Reply with the single word amber.")])
        assert "amber" in str(response.content).lower()
    finally:
        index.delete(tenant, doc)
    deadline = time.monotonic() + 90
    while chunk in index.query(tenant, kb, vector):
        assert time.monotonic() < deadline, "Deletion freshness deadline exceeded"
        time.sleep(2)


@pytest.mark.skipif(os.getenv("RUN_S3_TESTS") != "1", reason="S3 write test requires RUN_S3_TESTS=1")
def test_s3_roundtrip():
    assert settings().storage == "s3"
    storage = Storage()
    key = "integration-smoke/" + uuid.uuid4().hex
    try:
        storage.put(key, b"Synthetic object storage verification")
        assert storage.get(key) == b"Synthetic object storage verification"
    finally:
        storage.delete(key)
    from botocore.exceptions import ClientError

    with pytest.raises(ClientError) as error:
        storage.get(key)
    assert error.value.response["ResponseMetadata"]["HTTPStatusCode"] == 404


@pytest.mark.skipif(os.getenv("RUN_SCANNER_TESTS") != "1", reason="Real ClamAV requires RUN_SCANNER_TESTS=1")
def test_real_clamav_clean_and_eicar():
    from app.scanning import MalwareDetected, scan

    assert settings().scan_mode == "clamav"
    scan(b"Synthetic clean policy document")
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    with pytest.raises(MalwareDetected):
        scan(eicar)
