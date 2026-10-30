"""Bound request bodies before multipart parsing, including chunked uploads."""

import asyncio
from tempfile import SpooledTemporaryFile

from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app, max_upload_bytes: int, timeout: int):
        self.app, self.limit, self.timeout = app, max_upload_bytes + 65536, timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            return await self.app(scope, receive, send)
        limit = self.limit if scope["path"] == "/api/v1/documents" else 65536
        raw_length = dict(scope["headers"]).get(b"content-length")
        if raw_length:
            try:
                length = int(raw_length)
                if length < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({"detail": "Invalid content length"}, 400)(scope, receive, send)
            if length > limit:
                return await JSONResponse({"detail": "Request body too large"}, 413)(scope, receive, send)
        with SpooledTemporaryFile(max_size=1024 * 1024) as buffer:
            total = 0
            try:
                async with asyncio.timeout(self.timeout):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        data = message.get("body", b"")
                        total += len(data)
                        if total > limit:
                            return await JSONResponse({"detail": "Request body too large"}, 413)(
                                scope, receive, send
                            )
                        buffer.write(data)
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await JSONResponse({"detail": "Upload timed out"}, 408)(scope, receive, send)
            buffer.seek(0)
            remaining, finished = total, False

            async def replay():
                nonlocal remaining, finished
                if finished:
                    return await receive()
                data = buffer.read(65536)
                remaining -= len(data)
                finished = remaining == 0
                return {"type": "http.request", "body": data, "more_body": not finished}

            await self.app(scope, replay, send)
