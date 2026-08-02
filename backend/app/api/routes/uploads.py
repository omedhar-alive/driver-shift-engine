from fastapi import APIRouter, File, HTTPException, UploadFile

from app.integrations.google_cloud_storage import GoogleCloudStorageService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    storage_service = GoogleCloudStorageService()

    try:
        stored_image = storage_service.upload_dashboard_image(
            content=content,
            content_type=file.content_type or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "file_path": stored_image.public_url,
        "filename": stored_image.filename,
        "public_url": stored_image.public_url,
        "object_path": stored_image.object_path,
    }
