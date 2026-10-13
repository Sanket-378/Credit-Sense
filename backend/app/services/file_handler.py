import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from fastapi import UploadFile

MAGIC_TYPES = {
    "pdf": (b"%PDF-", ".pdf"),
    "jpeg": (b"\xff\xd8\xff", ".jpg"),
    "png": (b"\x89PNG\r\n\x1a\n", ".png"),
}
ALLOWED_EXTENSIONS = {".pdf": "pdf", ".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png"}
CHUNK_SIZE = 1024 * 1024


class UploadValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SavedUpload:
    path: Path
    file_type: str


def _detect_file_type(header: bytes) -> str | None:
    for file_type, (magic, _) in MAGIC_TYPES.items():
        if (file_type == "pdf" and magic in header[:1024]) or (
            file_type != "pdf" and header.startswith(magic)
        ):
            return file_type
    return None


async def validate_and_save_upload(upload: UploadFile, max_bytes: int) -> SavedUpload:
    filename = Path(upload.filename or "").name
    extension = Path(filename).suffix.lower()
    expected_type = ALLOWED_EXTENSIONS.get(extension)
    if expected_type is None:
        await upload.close()
        raise UploadValidationError("Only PDF, JPG, JPEG, and PNG documents are supported.")
    descriptor, temporary_name = tempfile.mkstemp(prefix="creditsense-", suffix=extension)
    path = Path(temporary_name)
    header = b""
    total_bytes = 0

    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            while chunk := await upload.read(CHUNK_SIZE):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise UploadValidationError("Each document must be within the configured file size limit.")
                if len(header) < 1024:
                    header += chunk[: 1024 - len(header)]
                temporary_file.write(chunk)

        detected_type = _detect_file_type(header)
        if expected_type is None or detected_type is None or detected_type != expected_type:
            raise UploadValidationError("Only PDF, JPG, JPEG, and PNG documents with matching file contents are supported.")
        if total_bytes == 0:
            raise UploadValidationError("Empty files cannot be verified.")
        return SavedUpload(path=path, file_type=detected_type)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def delete_temporary_upload(upload: SavedUpload) -> None:
    upload.path.unlink(missing_ok=True)
