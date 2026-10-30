import pytest

from app.adapters import parse
from app.config import Settings
from app.domain import chunks, terms


def test_deterministic_chunks_and_version_identity():
    pages = [(1, "Policy " * 400)]
    assert chunks("doc", 1, pages) == chunks("doc", 1, pages)
    assert chunks("doc", 1, pages)[0]["id"] != chunks("doc", 2, pages)[0]["id"]
    assert max(len(c["text"]) for c in chunks("doc", 1, pages)) <= 1200


def test_parser_rejects_binary_and_extracts_html_without_script():
    with pytest.raises(ValueError):
        parse("bad.txt", b"hello\x00bad")
    assert "evil" not in parse("a.html", b"<p>Policy</p><script>evil</script>")[0][1]
    with pytest.raises(ValueError):
        parse("fake.pdf", b"not pdf")


def test_production_rejects_development_configuration():
    with pytest.raises(ValueError):
        Settings(environment="production", dev_token="unsafe", provider="offline", _env_file=None)


def test_offline_terms():
    assert terms("What are the vacation policies?") == {"vacation", "policies"}
