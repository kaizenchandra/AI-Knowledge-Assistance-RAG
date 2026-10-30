import time
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from app import security


class FakeDB:
    def scalar(self, statement):
        return SimpleNamespace(tenant_id="tenant", role="viewer")


def test_oidc_signature_audience_and_expiry(monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    monkeypatch.setattr(
        security,
        "settings",
        lambda: SimpleNamespace(
            environment="production", dev_token="", oidc_audience="rag", oidc_issuer="https://issuer.example"
        ),
    )
    monkeypatch.setattr(
        security,
        "jwks",
        lambda: SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())),
    )
    claims = {
        "sub": "alice",
        "iss": "https://issuer.example",
        "aud": "rag",
        "iat": int(time.time()),
        "exp": int(time.time()) + 60,
    }
    token = jwt.encode(claims, private, algorithm="RS256")
    assert security.actor("Bearer " + token, "tenant", FakeDB()).subject == "alice"
    for changes in [{"exp": int(time.time()) - 60}, {"aud": "other"}, {"iss": "https://evil.example"}]:
        bad = jwt.encode({**claims, **changes}, private, algorithm="RS256")
        with pytest.raises(HTTPException) as error:
            security.actor("Bearer " + bad, "tenant", FakeDB())
        assert error.value.status_code == 401
    unsigned = jwt.encode(claims, "", algorithm="none")
    with pytest.raises(HTTPException):
        security.actor("Bearer " + unsigned, "tenant", FakeDB())
