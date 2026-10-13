import io

import fitz
from PIL import Image

from app.services.forensics import analyze_forensics


def _pdf_with_editor_metadata():
    document = fitz.open()
    document.new_page(width=100, height=100)
    document.set_metadata({"producer": "Canva Export"})
    return document.tobytes()


def test_pdf_editor_metadata_and_multiple_eof_are_reported(tmp_path):
    path = tmp_path / "editor.pdf"
    pdf = _pdf_with_editor_metadata()
    path.write_bytes(pdf + b"\n%%EOF\n")

    findings = analyze_forensics(path, "pdf", [])
    checks = {finding["check"] for finding in findings}
    assert "pdf_editor_metadata" in checks
    assert "pdf_incremental_updates" in checks


def test_missing_image_exif_is_not_a_finding(tmp_path):
    image_path = tmp_path / "plain.png"
    image = Image.new("RGB", (16, 16), "white")
    image.save(image_path, format="PNG")

    findings = analyze_forensics(image_path, "png", [image_path.read_bytes()])
    assert "image_editor_metadata" not in {finding["check"] for finding in findings}


def test_image_editor_exif_is_reported(tmp_path):
    image_path = tmp_path / "edited.jpg"
    image = Image.new("RGB", (20, 20), "white")
    exif = Image.Exif()
    exif[305] = "Adobe Photoshop"
    image.save(image_path, format="JPEG", exif=exif)

    findings = analyze_forensics(image_path, "jpeg", [image_path.read_bytes()])
    assert "image_editor_metadata" in {finding["check"] for finding in findings}
