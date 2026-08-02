from sqlalchemy.orm import Session

from app.models.shift_exception import ShiftException


class ShiftExceptionRepository:
    def create(
        self,
        db: Session,
        exception_type: str,
        message: str,
        driver_code: str | None = None,
        plate_number: str | None = None,
        related_start_id: str | None = None,
        related_end_id: str | None = None,
        raw_payload: str | None = None,
        status: str = "open",
    ) -> ShiftException:
        shift_exception = ShiftException(
            exception_type=exception_type,
            driver_code=driver_code,
            plate_number=plate_number,
            related_start_id=related_start_id,
            related_end_id=related_end_id,
            message=message,
            raw_payload=raw_payload,
            status=status,
        )
        db.add(shift_exception)
        db.commit()
        db.refresh(shift_exception)
        return shift_exception

    def list_open_sheet_sync_failures(self, db: Session) -> list[ShiftException]:
        return (
            db.query(ShiftException)
            .filter(
                ShiftException.status == "open",
                ShiftException.exception_type.in_(
                    [
                        "start_sheet_append_failed",
                        "end_sheet_append_failed",
                        "whole_shift_sheet_append_failed",
                    ]
                ),
            )
            .order_by(ShiftException.created_at.asc())
            .all()
        )

    def get_by_exception_id(self, db: Session, exception_id: str) -> ShiftException | None:
        return (
            db.query(ShiftException)
            .filter(ShiftException.exception_id == exception_id)
            .first()
        )

    def mark_as_resolved(self, db: Session, shift_exception: ShiftException) -> ShiftException:
        shift_exception.status = "resolved"
        db.commit()
        db.refresh(shift_exception)
        return shift_exception