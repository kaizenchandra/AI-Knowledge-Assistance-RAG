"""Read-only dependency checks. Never prints credentials or provider exception text."""

import json
import socket

from .adapters import Storage, vector_index
from .config import settings


def check_live_dependencies():
    cfg = settings()
    checks = {}
    if cfg.provider == "live":
        try:
            vector_index().validate()
            checks["pinecone"] = "ready"
        except Exception:
            checks["pinecone"] = "unavailable_or_incompatible"
    else:
        checks["pinecone"] = "not_enabled"
    if cfg.storage == "s3":
        try:
            storage = Storage()
            storage.client.head_bucket(Bucket=cfg.s3_bucket)
            checks["s3"] = "ready"
        except Exception:
            checks["s3"] = "unavailable"
    else:
        checks["s3"] = "not_enabled"
    checks["model"] = "configured_not_called" if cfg.provider == "live" else "not_enabled"
    checks["scanner"] = "not_enabled"
    if cfg.scan_mode == "clamav":
        try:
            with socket.create_connection((cfg.clamd_host, cfg.clamd_port), timeout=5) as conn:
                conn.settimeout(5)
                conn.sendall(b"zPING\0")
                result = b""
                while b"\0" not in result and len(result) < 32:
                    part = conn.recv(32)
                    if not part:
                        break
                    result += part
                if result != b"PONG\0":
                    raise ValueError("Unexpected scanner response")
            checks["scanner"] = "ready"
        except Exception:
            checks["scanner"] = "unavailable"
    return checks


if __name__ == "__main__":
    result = check_live_dependencies()
    print(json.dumps(result, indent=2))
    if any(value.startswith("unavailable") for value in result.values()):
        raise SystemExit(1)
