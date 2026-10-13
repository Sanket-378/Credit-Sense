import io
import threading
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz
from PIL import Image

_reader = None
_reader_init_lock = threading.Lock()
_reader_use_lock = threading.Lock()
MIN_TEXT_LENGTH = 40
MAX_PDF_PAGES = 5


@dataclass
class ReadResult:
    text: str
    page_images: list[bytes]
    ocr_status: str


def _get_ocr_reader(languages: list[str]):
    global _reader
    with _reader_init_lock:
        if _reader is None:
            import easyocr

            _reader = easyocr.Reader(languages, gpu=False)
    return _reader


def _image_text(image_bytes: bytes, languages: list[str]) -> str:
    reader = _get_ocr_reader(languages)
    with _reader_use_lock:
        words = reader.readtext(image_bytes, detail=0, paragraph=True)
    return "\n".join(str(word) for word in words if word)


def _ocr_status(text: str) -> str:
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        return "success"
    return "partial" if text.strip() else "failed"


def read_document(path: Path, file_type: str, languages: list[str]) -> ReadResult:
    if file_type == "pdf":
        return _read_pdf(path, languages)
    image_bytes = path.read_bytes()
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.load()
    text = _image_text(image_bytes, languages)
    return ReadResult(text=text, page_images=[image_bytes], ocr_status=_ocr_status(text))


def _read_pdf(path: Path, languages: list[str]) -> ReadResult:
    page_images: list[bytes] = []
    text_parts: list[str] = []
    with fitz.open(path) as document:
        for page in document:
            text_parts.append(page.get_text("text"))
        for page in document[:MAX_PDF_PAGES]:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            page_images.append(pixmap.tobytes("png"))

    text = "\n".join(part for part in text_parts if part).strip()
    if len(text) >= MIN_TEXT_LENGTH:
        return ReadResult(text=text, page_images=page_images, ocr_status="success")

    ocr_parts = [_image_text(image, languages) for image in page_images]
    combined = "\n".join(part for part in [text, *ocr_parts] if part).strip()
    return ReadResult(text=combined, page_images=page_images, ocr_status=_ocr_status(combined))
