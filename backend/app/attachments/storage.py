import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def save_file(service_entry_id: int, upload: UploadFile) -> tuple[str, str, str]:
    """Save an uploaded file under uploads_dir/<service_entry_id>/.

    Returns (relative_path, filename, content_type).
    """
    entry_dir = Path(settings.uploads_dir) / str(service_entry_id)
    entry_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(upload.filename or "file").name
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest = entry_dir / stored_name
    dest.write_bytes(upload.file.read())

    relative_path = f"{service_entry_id}/{stored_name}"
    return relative_path, safe_name, upload.content_type or "application/octet-stream"


def absolute_path(relative_path: str) -> Path:
    return Path(settings.uploads_dir) / relative_path


def delete_file(relative_path: str) -> None:
    path = absolute_path(relative_path)
    path.unlink(missing_ok=True)
