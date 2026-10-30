import asyncio
import io
import struct
from types import SimpleNamespace

import pytest
from docx import Document

from app import scanning
from app.body_limit import BodyLimitMiddleware
from app.isolated_parser import parse_isolated


def test_isolated_parser_supported_formats():
    assert "Policy" in parse_isolated("p.txt", b"Policy text")[0][1]
    assert "Policy" in parse_isolated("p.md", b"# Policy")[0][1]
    assert "evil" not in parse_isolated("p.html", b"<p>Policy</p><script>evil</script>")[0][1]
    document = Document()
    document.add_paragraph("Policy in Word")
    stream = io.BytesIO()
    document.save(stream)
    assert "Policy in Word" in parse_isolated("p.docx", stream.getvalue())[0][1]
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 10 100 Td (Policy in PDF) Tj ET")
    page[NameObject("/Contents")] = content
    pdf = io.BytesIO()
    writer.write(pdf)
    assert "Policy in PDF" in parse_isolated("p.pdf", pdf.getvalue())[0][1]
    with pytest.raises(ValueError):
        parse_isolated("p.pdf", b"bad pdf")


class ScannerConnection:
    def __init__(self, response):
        self.response, self.sent = response, b""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def settimeout(self, timeout):
        pass

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        result, self.response = self.response, b""
        return result


@pytest.mark.parametrize(
    "result,exception",
    [
        (b"stream: OK\0", None),
        (b"stream: Eicar FOUND\0", scanning.MalwareDetected),
        (b"stream: ERROR\0", RuntimeError),
        (b"", RuntimeError),
    ],
)
def test_scanner_fails_closed(monkeypatch, result, exception):
    connection = ScannerConnection(result)
    monkeypatch.setattr(
        scanning,
        "settings",
        lambda: SimpleNamespace(scan_mode="clamav", clamd_host="scanner", clamd_port=3310, scan_timeout=2),
    )
    monkeypatch.setattr(scanning.socket, "create_connection", lambda *a, **k: connection)
    if exception:
        with pytest.raises(exception):
            scanning.scan(b"safe sample")
    else:
        scanning.scan(b"safe sample")
        assert connection.sent == b"zINSTREAM\0" + struct.pack("!I", 11) + b"safe sample" + struct.pack(
            "!I", 0
        )


@pytest.mark.parametrize("declared", [True, False])
def test_request_body_rejected_before_application(declared):
    async def scenario():
        calls, sent = [], []

        async def app(scope, receive, send):
            calls.append(True)

        async def receive():
            return {"type": "http.request", "body": b"x" * 65537, "more_body": False}

        async def send(message):
            sent.append(message)

        middleware = BodyLimitMiddleware(app, 100, 2)
        await middleware(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/conversations",
                "headers": [(b"content-length", b"65537")] if declared else [],
            },
            receive,
            send,
        )
        assert not calls
        assert sent[0]["status"] == 413

    asyncio.run(scenario())
