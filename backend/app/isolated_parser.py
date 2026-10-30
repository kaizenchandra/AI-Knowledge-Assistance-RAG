import json
import os
import subprocess
import sys

from .config import settings


def parse_isolated(filename: str, data: bytes):
    cfg = settings()
    if len(data) > cfg.max_upload_bytes:
        raise ValueError("File too large")
    env = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "PARSER_MEMORY_MB": str(cfg.parser_memory_mb),
        "PARSER_TIMEOUT": str(cfg.parser_timeout),
        "MAX_UPLOAD_BYTES": str(cfg.max_upload_bytes),
        "MAX_TEXT_CHARS": str(cfg.max_text_chars),
    }
    try:
        result = subprocess.run(
            [sys.executable, "-m", "app.parser_process", filename],
            input=data,
            capture_output=True,
            timeout=cfg.parser_timeout + 2,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ValueError("Parser time limit exceeded") from None
    if result.returncode or len(result.stdout) > cfg.max_text_chars * 8 + 65536:
        raise ValueError("Document parsing failed or exceeded resource limits")
    pages = json.loads(result.stdout)
    if not isinstance(pages, list):
        raise ValueError("Invalid parser response")
    return pages
