from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app import adapters


def test_vector_scope_and_generation_filters():
    provider = adapters.PineconeIndex.__new__(adapters.PineconeIndex)
    provider.index = Mock()
    provider.index.query.return_value = SimpleNamespace(matches=[SimpleNamespace(id="chunk")])
    assert provider.query("tenant", "kb", [0.1]) == ["chunk"]
    args = provider.index.query.call_args.kwargs
    assert args["namespace"] == "tenant"
    assert args["filter"] == {
        "kb_id": {"$eq": "kb"},
        "embedding_version": {"$eq": adapters.embedding_version()},
    }
    provider.delete_version("tenant", "doc", 3)
    assert provider.index.delete.call_args.kwargs["filter"] == {
        "document_id": {"$eq": "doc"},
        "version": {"$eq": 3},
    }


def test_freshness_uses_exact_chunk_filter():
    provider = adapters.PineconeIndex.__new__(adapters.PineconeIndex)
    provider.index = Mock()
    provider.index.query.return_value = SimpleNamespace(matches=[])
    assert not provider.visible("tenant", "kb", [{"id": "chunk", "values": [1]}])
    assert provider.index.query.call_args.kwargs["filter"]["chunk_id"] == {"$eq": "chunk"}


def test_index_dimension_mismatch_rejected(monkeypatch):
    provider = adapters.PineconeIndex.__new__(adapters.PineconeIndex)
    provider.client = Mock()
    provider.client.describe_index.return_value = SimpleNamespace(
        host="index.example", dimension=10, metric="cosine", status={"ready": True}
    )
    monkeypatch.setattr(
        adapters,
        "settings",
        lambda: SimpleNamespace(
            pinecone_index="index", pinecone_host="https://index.example", embedding_dimensions=20
        ),
    )
    with pytest.raises(ValueError, match="dimension"):
        provider.validate()
