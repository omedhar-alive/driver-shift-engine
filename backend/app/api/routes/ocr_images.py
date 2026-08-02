import base64

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.integrations.google_cloud_storage import GoogleCloudStorageService
from app.repositories.shift_end_repository import ShiftEndRepository
from app.repositories.shift_start_repository import ShiftStartRepository


router = APIRouter(prefix="/ocr-images", tags=["OCR Images"])


@router.get("/shift-starts/{start_id}")
def get_shift_start_ocr_image(
    start_id: str,
    db: Session = Depends(get_db),
) -> Response:
    repository = ShiftStartRepository()
    shift_start = repository.get_by_start_id(db=db, start_id=start_id)

    if shift_start is None:
        raise HTTPException(status_code=404, detail="Shift start not found")

    return _build_image_response(
        image_reference=shift_start.start_dashboard_image,
        encoded_image=shift_start.ocr_image_data,
        mime_type=shift_start.ocr_image_mime_type,
        missing_detail="OCR image not found for this shift start",
    )


@router.get("/shift-ends/{end_id}")
def get_shift_end_ocr_image(
    end_id: str,
    db: Session = Depends(get_db),
) -> Response:
    repository = ShiftEndRepository()
    shift_end = repository.get_by_end_id(db=db, end_id=end_id)

    if shift_end is None:
        raise HTTPException(status_code=404, detail="Shift end not found")

    return _build_image_response(
        image_reference=shift_end.end_dashboard_image,
        encoded_image=shift_end.ocr_image_data,
        mime_type=shift_end.ocr_image_mime_type,
        missing_detail="OCR image not found for this shift end",
    )


def _build_image_response(
    image_reference: str,
    encoded_image: str | None,
    mime_type: str | None,
    missing_detail: str,
) -> Response:
    if encoded_image and mime_type:
        try:
            image_bytes = base64.b64decode(encoded_image)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Stored OCR image is invalid") from exc

        return Response(content=image_bytes, media_type=mime_type)

    storage_service = GoogleCloudStorageService()
    stored_image = storage_service.load_image(image_reference)
    if stored_image is None:
        raise HTTPException(status_code=404, detail=missing_detail)

    return Response(content=stored_image.content, media_type=stored_image.mime_type)
