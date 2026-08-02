import json
from sqlalchemy.orm import Session

from app.models.shift_exception import ShiftException
from app.repositories.shift_exception_repository import ShiftExceptionRepository


class ShiftExceptionService:
    def __init__(self) -> None:
        self.repository = ShiftExceptionRepository()

    def create_exception(
        self,
        db: Session,
        exception_type: str,
        message: str,
        driver_code: str | None = None,
        plate_number: str | None = None,
        related_start_id: str | None = None,
        related_end_id: str | None = None,
        raw_payload: dict | None = None,
        status: str = "open",
    ) -> ShiftException:
        raw_payload_text = json.dumps(raw_payload) if raw_payload is not None else None

        return self.repository.create(
            db=db,
            exception_type=exception_type,
            message=message,
            driver_code=driver_code,
            plate_number=plate_number,
            related_start_id=related_start_id,
            related_end_id=related_end_id,
            raw_payload=raw_payload_text,
            status=status,
        )