import io
import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pymupdf as fitz
from PIL import Image, ImageChops, ImageStat

logger = logging.getLogger(__name__)

EDITORS = (
    "microsoft word",
    "wps",
    "foxit",
    "pdfescape",
    "smallpdf",
    "sejda",
    "ilovepdf",
    "pdf-xchange",
    "pdf xchange",
    "nitro",
    "pdf-lib",
    "skia/pdf",
    "microsoft: print to pdf",
    "libreoffice",
    "canva",
    "photoshop",
    "gimp",
    "illustrator",
)
ELA_RATIO_THRESHOLD = 4.0
ELA_MIN_BLOCK_MEAN = 12.0
AMOUNT_TOKEN_PATTERN = re.compile(r"(?<!\w)\d[\d,]*(?:\.\d{1,2})?(?!\w)")
PDF_DATE_PATTERN = re.compile(
    r"D:(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?"
)
OBJECT_PATTERN = re.compile(rb"(?m)(\d+)\s+(\d+)\s+obj\b")
OBJECT_REFERENCE_PATTERN = re.compile(rb"(?<!\d)(\d+)\s+(\d+)\s+R\b")
XREF_PATTERN = re.compile(rb"(?m)(?:^|\s)xref(?:\s|$)")
XREF_STREAM_PATTERN = re.compile(rb"/Type\s*/XRef\b")
PREV_PATTERN = re.compile(rb"/Prev\s+\d+")
BYTE_RANGE_PATTERN = re.compile(
    rb"/ByteRange\s*\[\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\]"
)
SIGNATURE_PATTERN = re.compile(rb"/Type\s*/Sig\b")
XMP_HISTORY_PATTERN = re.compile(r"xmpMM:History|stEvt:action", re.IGNORECASE)
WHITE_COLOR = (1.0, 1.0, 1.0)
COLOR_TOLERANCE = 0.02
MIN_FONT_CONSISTENCY_SAMPLES = 3


def _finding(
    check: str,
    detail: str,
    severity: str = "medium",
) -> dict[str, str]:
    return {
        "check": check,
        "severity": severity,
        "detail": detail,
        "category": "forensics",
    }


def _parse_pdf_date(value: str | None) -> datetime | None:
    if not value:
        return None
    match = PDF_DATE_PATTERN.search(value)
    if not match:
        return None
    parts = [
        int(part or default)
        for part, default in zip(
            match.groups(),
            ("1", "1", "0", "0", "0", "0"),
        )
    ]
    try:
        return datetime(*parts)
    except ValueError:
        return None


def _contains_editor(value: str, doc_type: str | None = None) -> bool:
    lowered = value.casefold()
    if any(editor in lowered for editor in EDITORS):
        return True
    return doc_type in {"bank_statement", "upi_statement"} and any(
        editor in lowered for editor in ("acrobat", "distiller")
    )


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
            difference = ImageChops.difference(
                original,
                recompressed.convert("RGB"),
            ).convert("L")
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
        if (
            maximum_block_mean >= ELA_MIN_BLOCK_MEAN
            and maximum_block_mean >= global_mean * ratio_threshold
        ):
            return _finding(
                "error_level_analysis",
                "Error-level analysis found a localized high-error area suggesting possible region manipulation; this is not proof of editing.",
            )
    except (OSError, ValueError):
        return None
    return None


def _metadata_findings(
    metadata: dict[str, Any],
    doc_type: str,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    producer = str(metadata.get("producer") or "")
    creator = str(metadata.get("creator") or "")
    if _contains_editor(producer, doc_type) or _contains_editor(creator, doc_type):
        findings.append(
            _finding(
                "pdf_editor_metadata",
                "PDF producer or creator metadata names software commonly used to edit or re-save PDFs.",
                "high",
            )
        )
    if producer and creator and producer.strip().casefold() != creator.strip().casefold():
        findings.append(
            _finding(
                "pdf_producer_creator_mismatch",
                "PDF producer and creator metadata differ, which can indicate re-saving.",
                "medium",
            )
        )

    created = _parse_pdf_date(metadata.get("creationDate"))
    modified = _parse_pdf_date(metadata.get("modDate"))
    if created is None:
        findings.append(
            _finding(
                "pdf_creation_date_missing",
                "PDF creation date metadata is missing or invalid.",
                "low",
            )
        )
    elif modified is not None and created != modified:
        findings.append(
            _finding(
                "pdf_creation_modification_date_mismatch",
                "PDF creation and modification dates differ.",
                "medium",
            )
        )
    return findings


def _known_generator_signal(
    document: fitz.Document,
    doc_type: str,
    fingerprint_path: Path | None = None,
) -> tuple[list[dict[str, str]], list[str], dict[str, Any]]:
    path = fingerprint_path or Path(__file__).resolve().parents[1] / "data" / "known_generators.json"
    raw_signals: dict[str, Any] = {"known_generator": None, "matched": False}
    if not path.exists():
        return [], [], raw_signals
    try:
        fingerprints = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], [], raw_signals

    metadata = document.metadata or {}
    producer = str(metadata.get("producer") or "").strip().casefold()
    creator = str(metadata.get("creator") or "").strip().casefold()
    font_names = {
        str(font[3]).casefold()
        for page in document
        for font in page.get_fonts(full=True)
    }
    first_page_text = document[0].get_text("text").casefold() if len(document) else ""
    sources = fingerprints.get("sources", {})
    for source, fingerprint in sources.items():
        if doc_type not in fingerprint.get("doc_types", [doc_type]):
            continue
        aliases = [source, *fingerprint.get("aliases", [])]
        if not any(alias.casefold() in first_page_text for alias in aliases):
            continue
        expected_producers = {
            str(value).strip().casefold()
            for value in fingerprint.get("producers", [])
        }
        expected_creators = {
            str(value).strip().casefold()
            for value in fingerprint.get("creators", [])
        }
        expected_fonts = {
            str(value).strip().casefold()
            for value in fingerprint.get("font_set", [])
        }
        producer_matches = not expected_producers or producer in expected_producers
        creator_matches = not expected_creators or creator in expected_creators
        fonts_match = not expected_fonts or font_names == expected_fonts
        raw_signals["known_generator"] = source
        raw_signals["producer_matches"] = producer_matches
        raw_signals["creator_matches"] = creator_matches
        raw_signals["font_set_matches"] = fonts_match
        if producer_matches and creator_matches and fonts_match:
            raw_signals["matched"] = True
            return [], ["generator_matches_known_source"], raw_signals
        return [
            _finding(
                "known_generator_mismatch",
                "PDF generator metadata or fonts differ from the registered profile for the claimed source.",
                "medium",
            )
        ], [], raw_signals
    return [], [], raw_signals


def _signature_status(
    path: Path,
    raw_bytes: bytes,
) -> tuple[list[dict[str, str]], list[str], dict[str, Any]]:
    matches = list(BYTE_RANGE_PATTERN.finditer(raw_bytes))
    has_signature = bool(matches) or bool(SIGNATURE_PATTERN.search(raw_bytes))
    if not has_signature:
        return [], [], {"present": False, "status": "not_present"}

    statuses = []
    for match in matches:
        start_a, length_a, start_b, length_b = map(int, match.groups())
        covered_end = start_b + length_b
        structurally_valid = (
            start_a == 0
            and length_a <= start_b
            and covered_end <= len(raw_bytes)
            and start_b >= length_a
        )
        covers_current_file = structurally_valid and covered_end == len(raw_bytes)
        statuses.append({
            "byte_range_valid": structurally_valid,
            "covers_current_file": covers_current_file,
        })

    if not statuses or any(
        not status["byte_range_valid"] or not status["covers_current_file"]
        for status in statuses
    ):
        return [
            _finding(
                "pdf_signature_broken",
                "A PDF signature is present but its byte range is invalid or does not cover the current file.",
                "high",
            )
        ], [], {
            "present": True,
            "status": "broken_or_modified",
            "signatures": statuses,
        }
    try:
        from pyhanko.pdf_utils.reader import PdfFileReader
        from pyhanko.sign.validation import validate_pdf_signature

        with path.open("rb") as stream:
            reader = PdfFileReader(stream)
            embedded_signatures = reader.embedded_signatures
            verified_signatures = [
                validate_pdf_signature(signature)
                for signature in embedded_signatures
            ]
        cryptographically_valid = bool(verified_signatures) and all(
            signature.intact and signature.valid
            for signature in verified_signatures
        )
        if cryptographically_valid:
            return [], ["valid_digital_signature"], {
                "present": True,
                "status": "cryptographically_valid",
                "signatures": statuses,
            }
        return [
            _finding(
                "pdf_signature_broken",
                "A PDF signature is present but its cryptographic integrity or validity check failed.",
                "high",
            )
        ], [], {
            "present": True,
            "status": "cryptographically_invalid",
            "signatures": statuses,
        }
    except (OSError, ValueError, RuntimeError) as error:
        logger.warning("PDF signature verification could not be completed: %s", type(error).__name__)
        return [
            _finding(
                "pdf_signature_verification_failed",
                "A PDF signature is present but could not be cryptographically verified.",
                "high",
            )
        ], [], {
            "present": True,
            "status": "verification_failed",
            "signatures": statuses,
        }


def _structure_signals(raw_bytes: bytes) -> tuple[list[dict[str, str]], dict[str, Any]]:
    eof_count = raw_bytes.count(b"%%EOF")
    xref_count = len(XREF_PATTERN.findall(raw_bytes)) + len(XREF_STREAM_PATTERN.findall(raw_bytes))
    prev_count = len(PREV_PATTERN.findall(raw_bytes))
    object_definitions = [
        (int(match.group(1)), int(match.group(2)))
        for match in OBJECT_PATTERN.finditer(raw_bytes)
    ]
    object_counts = Counter(object_number for object_number, _ in object_definitions)
    replaced_object_count = sum(count - 1 for count in object_counts.values() if count > 1)
    nonzero_generations = sum(generation > 0 for _, generation in object_definitions)
    defined_objects = set(object_definitions)
    orphaned_object_count = sum(
        (int(match.group(1)), int(match.group(2))) not in defined_objects
        for match in OBJECT_REFERENCE_PATTERN.finditer(raw_bytes)
    )
    signals = {
        "eof_count": eof_count,
        "xref_section_count": xref_count,
        "prev_entry_count": prev_count,
        "nonzero_generation_object_count": nonzero_generations,
        "replaced_object_count": replaced_object_count,
        "orphaned_object_count": orphaned_object_count,
        "signature_count": len(list(BYTE_RANGE_PATTERN.finditer(raw_bytes))),
    }
    findings: list[dict[str, str]] = []
    if eof_count > 1 or prev_count:
        findings.append(
            _finding(
                "pdf_incremental_updates",
                "PDF cross-reference structure contains incremental revisions.",
                "medium",
            )
        )
    if replaced_object_count:
        findings.append(
            _finding(
                "pdf_replaced_objects",
                f"PDF structure redefines {replaced_object_count} object(s) across revisions.",
                "medium",
            )
        )
    if nonzero_generations:
        findings.append(
            _finding(
                "pdf_nonzero_generation_objects",
                f"PDF structure contains {nonzero_generations} object(s) with nonzero generation numbers.",
                "low",
            )
        )
    return findings, signals


def _numeric_tokens(value: str) -> list[str]:
    return [
        token.replace(",", "").strip(".")
        for token in AMOUNT_TOKEN_PATTERN.findall(value)
    ]


def _is_amount_span(text: str) -> bool:
    return bool(
        "₹" in text
        or re.search(r"\d[\d,]*\.\d{1,2}\b", text)
        or re.search(r"\d{1,3}(?:,\d{3})+\b", text)
    )


def _page_background_color(page: fitz.Page) -> tuple[float, float, float]:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
    return tuple(channel / 255 for channel in pixmap.pixel(0, 0)[:3])


def _text_style_signals(page: fitz.Page) -> tuple[list[dict[str, str]], dict[str, Any]]:
    amount_spans: list[tuple[str, float, int]] = []
    text_spans: list[tuple[fitz.Rect, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = str(span.get("text") or "")
                if not text.strip():
                    continue
                rect = fitz.Rect(span["bbox"])
                text_spans.append((rect, text))
                if _is_amount_span(text):
                    amount_spans.append(
                        (
                            str(span.get("font") or ""),
                            round(float(span.get("size") or 0), 2),
                            int(span.get("color") or 0),
                        )
                    )

    font_counts = Counter(font for font, _, _ in amount_spans)
    size_counts = Counter(size for _, size, _ in amount_spans)
    color_counts = Counter(color for _, _, color in amount_spans)
    dominant_font = font_counts.most_common(1)[0][0] if font_counts else None
    dominant_size = size_counts.most_common(1)[0][0] if size_counts else None
    dominant_color = color_counts.most_common(1)[0][0] if color_counts else None
    anomalous_amount_span_count = sum(
        font != dominant_font or size != dominant_size or color != dominant_color
        for font, size, color in amount_spans
    ) if len(amount_spans) >= MIN_FONT_CONSISTENCY_SAMPLES else 0

    overlaps = 0
    for index, (rect, _) in enumerate(text_spans):
        for other_rect, _ in text_spans[index + 1:]:
            intersection = rect & other_rect
            if intersection.is_empty:
                continue
            smaller_area = min(rect.get_area(), other_rect.get_area())
            if smaller_area and intersection.get_area() / smaller_area > 0.5:
                overlaps += 1

    background_rectangle_overlaps = 0
    background_color = _page_background_color(page)
    background = page.rect
    for drawing in page.get_drawings():
        fill = drawing.get("fill")
        rect = fitz.Rect(drawing["rect"])
        if fill is None or not rect.intersects(background):
            continue
        fill_color = tuple(fill[:3])
        if not all(
            abs(channel - background_color[index]) <= COLOR_TOLERANCE
            or abs(channel - WHITE_COLOR[index]) <= COLOR_TOLERANCE
            for index, channel in enumerate(fill_color)
        ):
            continue
        if any(rect.intersects(span_rect) for span_rect, _ in text_spans):
            background_rectangle_overlaps += 1

    findings: list[dict[str, str]] = []
    if anomalous_amount_span_count:
        findings.append(
            _finding(
                "pdf_amount_font_inconsistency",
                f"Possible edited text affects the currency amount field type ({anomalous_amount_span_count} span(s) differ from the page's dominant amount style).",
                "medium",
            )
        )
    if background_rectangle_overlaps:
        findings.append(
            _finding(
                "pdf_white_overlay",
                f"{background_rectangle_overlaps} filled page-background rectangle(s) overlap text spans.",
                "high",
            )
        )
    if overlaps:
        findings.append(
            _finding(
                "pdf_overlapping_text",
                f"{overlaps} text span pair(s) overlap substantially.",
                "high",
            )
        )

    return findings, {
        "font_set": sorted({
            str(font[3])
            for font in page.get_fonts(full=True)
        }),
        "amount_font_set": sorted(font_counts),
        "amount_span_count": len(amount_spans),
        "anomalous_amount_span_count": anomalous_amount_span_count,
        "text_span_overlap_count": overlaps,
        "white_rectangle_overlap_count": background_rectangle_overlaps,
    }


def _page_content_stream_count(page: fitz.Page) -> int:
    try:
        return len(page.get_contents())
    except (RuntimeError, ValueError):
        return 0


def _ocr_numeric_tokens(page: fitz.Page) -> list[str] | None:
    from .reader import _image_text

    try:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72), alpha=False)
        text = _image_text(pixmap.tobytes("png"), ["en"])
    except Exception as error:
        logger.warning("Rendered-page OCR was unavailable: %s", type(error).__name__)
        return None
    return _numeric_tokens(text)


def _visual_text_comparison(
    page: fitz.Page,
    layer_text: str,
) -> tuple[dict[str, int | None], dict[str, str] | None]:
    visible_tokens = _ocr_numeric_tokens(page)
    if visible_tokens is None:
        return {
            "text_layer_numeric_token_count": len(_numeric_tokens(layer_text)),
            "visual_numeric_token_count": None,
            "text_only_numeric_token_count": None,
            "visual_only_numeric_token_count": None,
        }, None
    layer_counts = Counter(_numeric_tokens(layer_text))
    visible_counts = Counter(visible_tokens)
    text_only = sum((layer_counts - visible_counts).values())
    visual_only = sum((visible_counts - layer_counts).values())
    signals = {
        "text_layer_numeric_token_count": sum(layer_counts.values()),
        "visual_numeric_token_count": sum(visible_counts.values()),
        "text_only_numeric_token_count": text_only,
        "visual_only_numeric_token_count": visual_only,
    }
    if text_only or visual_only:
        return signals, _finding(
            "pdf_visual_text_mismatch",
            f"Rendered-page OCR and PDF text differ for {text_only + visual_only} numeric token(s) ({text_only} text-only, {visual_only} visual-only).",
            "high",
        )
    return signals, None


def analyze_pdf_report(
    path: Path,
    doc_type: str = "bank_statement",
    fingerprint_path: Path | None = None,
    page_images: list[bytes] | None = None,
) -> dict[str, Any]:
    raw_bytes = path.read_bytes()
    findings, structure = _structure_signals(raw_bytes)
    positive_signals: list[str] = []
    raw_signals: dict[str, Any] = {
        "metadata": {},
        "structure": structure,
        "pages": [],
        "visual_text_mismatches": {
            "text_only_numeric_token_count": 0,
            "visual_only_numeric_token_count": 0,
            "pages_compared": 0,
        },
    }
    with fitz.open(path) as document:
        metadata = document.metadata or {}
        raw_signals["metadata"] = {
            field: metadata.get(field)
            for field in (
                "producer",
                "creator",
                "creationDate",
                "modDate",
                "format",
                "encryption",
            )
        }
        findings.extend(_metadata_findings(metadata, doc_type))
        xmp_metadata = document.get_xml_metadata() or ""
        if XMP_HISTORY_PATTERN.search(xmp_metadata):
            findings.append(
                _finding(
                    "pdf_xmp_edit_history",
                    "XMP metadata contains document edit-history entries.",
                    "medium",
                )
            )
        generator_findings, generator_signals, generator_details = _known_generator_signal(
            document,
            doc_type,
            fingerprint_path,
        )
        findings.extend(generator_findings)
        positive_signals.extend(generator_signals)
        raw_signals["known_generator"] = generator_details

        for page_number, page in enumerate(document, start=1):
            page_findings, style_signals = _text_style_signals(page)
            findings.extend(page_findings)
            layer_text = page.get_text("text")
            visual_signals, mismatch_finding = _visual_text_comparison(page, layer_text)
            if mismatch_finding:
                findings.append(mismatch_finding)
            if visual_signals["visual_numeric_token_count"] is not None:
                raw_signals["visual_text_mismatches"]["pages_compared"] += 1
                raw_signals["visual_text_mismatches"]["text_only_numeric_token_count"] += (
                    visual_signals["text_only_numeric_token_count"] or 0
                )
                raw_signals["visual_text_mismatches"]["visual_only_numeric_token_count"] += (
                    visual_signals["visual_only_numeric_token_count"] or 0
                )
            raw_signals["pages"].append({
                "page": page_number,
                "font_signals": style_signals,
                "content_stream_count": _page_content_stream_count(page),
                "visual_text_signals": visual_signals,
            })

    signature_findings, signature_signals, signature_details = _signature_status(path, raw_bytes)
    findings.extend(signature_findings)
    positive_signals.extend(signature_signals)
    raw_signals["digital_signature"] = signature_details
    for image in page_images or []:
        ela = _ela_finding(image)
        if ela:
            findings.append(ela)
            break

    unique_findings = []
    seen_findings = set()
    for finding in findings:
        key = (finding["check"], finding["detail"])
        if key not in seen_findings:
            seen_findings.add(key)
            unique_findings.append(finding)

    return {
        "findings": unique_findings,
        "positive_signals": sorted(set(positive_signals)),
        "raw_signals": raw_signals,
    }


def analyze_forensics(
    path: Path,
    file_type: str,
    page_images: list[bytes],
    ela_ratio_threshold: float = ELA_RATIO_THRESHOLD,
    doc_type: str = "bank_statement",
) -> list[dict[str, str]]:
    if file_type == "pdf":
        report = analyze_pdf_report(path, doc_type)
        findings = report["findings"]
    else:
        findings = []
        raw_bytes = path.read_bytes()
        try:
            with Image.open(io.BytesIO(raw_bytes)) as image:
                software = str(image.getexif().get(305, ""))
        except (OSError, ValueError):
            software = ""
        if _contains_editor(software):
            findings.append(
                _finding(
                    "image_editor_metadata",
                    "Image EXIF software metadata names a document editor.",
                )
            )
        ela = _ela_finding(raw_bytes, ela_ratio_threshold)
        if ela:
            findings.append(ela)

    for image in page_images:
        ela = _ela_finding(image, ela_ratio_threshold)
        if ela and not any(finding["check"] == ela["check"] for finding in findings):
            findings.append(ela)
            break
    return findings
