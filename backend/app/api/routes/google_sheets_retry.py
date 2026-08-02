from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.services.google_sheets_retry_service import GoogleSheetsRetryService

router = APIRouter(prefix="/google-sheets-retry", tags=["Google Sheets Retry"])


@router.post("/")
def retry_google_sheets_sync(
    db: Session = Depends(get_db),
) -> dict:
    service = GoogleSheetsRetryService()
    return service.retry_open_sheet_sync_failures(db=db)