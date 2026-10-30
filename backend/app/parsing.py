import io
import pathlib
import zipfile

from bs4 import BeautifulSoup
from docx import Document as WordDocument
from pypdf import PdfReader


def extract(filename: str, data: bytes, max_upload_bytes: int, max_text_chars: int):
    ext = pathlib.Path(filename).suffix.lower()
    if len(data) > max_upload_bytes:
        raise ValueError("File too large")
    if ext == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF")
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted or len(reader.pages) > 500:
            raise ValueError("Encrypted or oversized PDF")
        pages = [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
    elif ext == ".docx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if len(archive.infolist()) > 1000 or sum(x.file_size for x in archive.infolist()) > 50_000_000:
                raise ValueError("Archive expansion limit")
        pages = [(None, "\n".join(p.text for p in WordDocument(io.BytesIO(data)).paragraphs))]
    elif ext in {".txt", ".md", ".html"}:
        text = data.decode("utf-8")
        if "\x00" in text:
            raise ValueError("Binary content rejected")
        if ext == ".html":
            soup = BeautifulSoup(text, "html.parser")
            for node in soup(["script", "style", "iframe", "object"]):
                node.decompose()
            text = soup.get_text(" ")
        pages = [(None, text)]
    else:
        raise ValueError("Unsupported file type")
    if sum(len(text) for _, text in pages) > max_text_chars:
        raise ValueError("Extracted text limit")
    if not any(text.strip() for _, text in pages):
        raise ValueError("No extractable text; OCR is not enabled")
    return pages
