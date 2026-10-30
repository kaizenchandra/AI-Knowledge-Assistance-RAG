"""ClamAV INSTREAM client. Scanner failures never count as clean results."""

import socket
import struct
import time

from .config import settings


class MalwareDetected(ValueError):
    pass


def scan(data: bytes):
    cfg = settings()
    if cfg.scan_mode == "disabled":
        if cfg.environment != "development":
            raise RuntimeError("Scanner required")
        return
    with socket.create_connection((cfg.clamd_host, cfg.clamd_port), timeout=cfg.scan_timeout) as conn:
        deadline = time.monotonic() + cfg.scan_timeout

        def remaining():
            seconds = deadline - time.monotonic()
            if seconds <= 0:
                raise TimeoutError("Scanner time limit exceeded")
            conn.settimeout(seconds)

        remaining()
        conn.sendall(b"zINSTREAM\0")
        for offset in range(0, len(data), 65536):
            remaining()
            part = data[offset : offset + 65536]
            conn.sendall(struct.pack("!I", len(part)) + part)
        conn.sendall(struct.pack("!I", 0))
        response = b""
        while b"\0" not in response:
            remaining()
            packet = conn.recv(1024)
            if not packet or len(response) + len(packet) > 4096:
                raise RuntimeError("Invalid scanner response")
            response += packet
        result = response.split(b"\0", 1)[0]
        if result.endswith(b" FOUND"):
            raise MalwareDetected("Document quarantined by malware scanner")
        if result != b"stream: OK":
            raise RuntimeError("Scanner did not confirm clean content")
