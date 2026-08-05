from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.attachments import storage
from app.attachments.models import Attachment
from app.core.database import get_db
from app.core.security import CurrentUser
from app.maintenance.models import ServiceEntry
from app.maintenance.schemas import AttachmentRead

router = APIRouter(tags=["attachments"])


@router.post(
    "/service-entries/{entry_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    entry_id: int, file: UploadFile, user: CurrentUser, db: Session = Depends(get_db)
) -> Attachment:
    entry = db.get(ServiceEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Service entry not found")

    relative_path, filename, content_type = storage.save_file(entry_id, file)
    attachment = Attachment(
        service_entry_id=entry_id,
        filename=filename,
        content_type=content_type,
        path=relative_path,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int, user: CurrentUser, db: Session = Depends(get_db)
) -> FileResponse:
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = storage.absolute_path(attachment.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.filename)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int, user: CurrentUser, db: Session = Depends(get_db)
) -> None:
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    storage.delete_file(attachment.path)
    db.delete(attachment)
    db.commit()
