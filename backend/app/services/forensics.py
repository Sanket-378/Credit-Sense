import io
import re
from datetime import datetime
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageChops, ImageStat

EDITORS = ("photoshop", "canva", "gimp", "illustrator", "ilovepdf", "sejda")
ELA_RATIO_THRESHOLD = 4.0
ELA_MIN_BLOCK_MEAN = 12.0


def _finding(check: str, detail: str, severity: str = "medium") -> dict[str, str]:
    return {"check": check, "severity": severity, "detail": detail}


def _contains_editor(value: str) -> bool:
    lowered = value.lower()
    return any(editor in lowered for editor in EDITORS)


def _parse_pdf_date(value: str | None) -> datetime | None:
    if not value:
        return None
    match = re.search(r"D:(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?", value)
    if not match:
        return None
    parts = [int(part or default) for part, default in zip(match.groups(), ("1", "1", "0", "0", "0"))]
    try:
        return datetime(*parts)
    except ValueError:
        return None


def _ela_finding(
    image_bytes: bytes,
    ratio_threshold: float = ELA_RATIO_THRESHOLD,
) -> dict[str, str] | None:
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.load()
            original = source.convert("RGB")
        if max(original.size) > 768:
            original.thumbnail((768, 768))
        encoded = io.BytesIO()
        original.save(encoded, format="JPEG", quality=90)
        encoded.seek(0)
        with Image.open(encoded) as recompressed:
            difference = ImageChops.difference(original, recompressed.convert("RGB")).convert("L")
        global_mean = ImageStat.Stat(difference).mean[0]
        if global_mean < 1:
            return None
        width, height = difference.size
        block_width = max(1, width // 8)
        block_height = max(1, height // 8)
        maximum_block_mean = 0.0
        for row in range(8):
            for column in range(8):
                box = (
                    column * block_width,
                    row * block_height,
                    width if column == 7 else (column + 1) * block_width,
                    height if row == 7 else (row + 1) * block_height,
                )
                maximum_block_mean = max(
                    maximum_block_mean,
                    ImageStat.Stat(difference.crop(box)).mean[0],
                )
        if maximum_block_mean >= ELA_MIN_BLOCK_MEAN and maximum_block_mean >= global_mean * ratio_threshold:
            return _finding(
                "error_level_analysis",
                "Error-level analysis found a localized high-error area suggesting possible region manipulation; this is not proof of editing.",
            )
    except (OSError, ValueError):
        return None
    return None


def analyze_forensics(
    path: Path,
    file_type: str,
    page_images: list[bytes],
    ela_ratio_threshold: float = ELA_RATIO_THRESHOLD,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    raw_bytes = path.read_bytes()

    if file_type == "pdf":
        if raw_bytes.count(b"%%EOF") > 1:
            findings.append(
                _finding("pdf_incremental_updates", "The PDF contains multiple end-of-file markers, which can indicate incremental updates.")
            )
        try:
            with fitz.open(path) as document:
                metadata = document.metadata or {}
        except (fitz.FileDataError, OSError):
            metadata = {}
        for field in ("producer", "creator"):
            value = str(metadata.get(field) or "")
            if _contains_editor(value):
                findings.append(
                    _finding("pdf_editor_metadata", f"PDF {field} metadata names a document editor.")
                )
        created = _parse_pdf_date(metadata.get("creationDate"))
        modified = _parse_pdf_date(metadata.get("modDate"))
        if created and modified and modified > created:
            findings.append(
                _finding("pdf_modified_after_creation", "PDF metadata shows a modification date later than its creation date.")
            )
    else:
        try:
            with Image.open(io.BytesIO(raw_bytes)) as image:
                software = str(image.getexif().get(305, ""))
        except (OSError, ValueError):
            software = ""
        if _contains_editor(software):
            findings.append(
                _finding("image_editor_metadata", "Image EXIF software metadata names a document editor.")
            )
        ela = _ela_finding(raw_bytes, ela_ratio_threshold)
        if ela:
            findings.append(ela)

    if file_type == "pdf":
        for image in page_images:
            ela = _ela_finding(image, ela_ratio_threshold)
            if ela:
                findings.append(ela)
                break
    return findings
