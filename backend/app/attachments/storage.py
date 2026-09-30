import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
# Mirrors the accept="image/*,application/pdf" hint on AttachmentUploader,
# which is only a file-picker filter and enforces nothing.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}
_CHUNK_BYTES = 1024 * 1024


def save_file(service_entry_id: int, upload: UploadFile) -> tuple[str, str, str]:
    """Save an uploaded file under uploads_dir/<service_entry_id>/.

    Streams in chunks and stops at MAX_UPLOAD_BYTES so a mis-picked huge
    file can neither be read whole into memory nor fill the data volume
    that also holds the SQLite DB.

    Returns (relative_path, filename, content_type).
    """
    content_type = upload.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Nepodporovaný typ souboru: {content_type}")

    entry_dir = Path(settings.uploads_dir) / str(service_entry_id)
    entry_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(upload.filename or "file").name
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest = entry_dir / stored_name

    written = 0
    try:
        with dest.open("wb") as fh:
            while chunk := upload.file.read(_CHUNK_BYTES):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise ValueError(
                        "Soubor je příliš velký "
                        f"(max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)"
                    )
                _ = fh.write(chunk)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise

    relative_path = f"{service_entry_id}/{stored_name}"
    return relative_path, safe_name, content_type


def absolute_path(relative_path: str) -> Path:
    return Path(settings.uploads_dir) / relative_path


def delete_file(relative_path: str) -> None:
    path = absolute_path(relative_path)
    path.unlink(missing_ok=True)


def delete_entry_dir(service_entry_id: int) -> None:
    shutil.rmtree(Path(settings.uploads_dir) / str(service_entry_id), ignore_errors=True)
