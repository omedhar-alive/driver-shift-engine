from sqlalchemy.orm import Session

from app.integrations.google_sheets.end_events import EndEventsSheetService
from app.integrations.google_sheets.start_events import StartEventsSheetService
from app.integrations.google_sheets.whole_shifts import WholeShiftsSheetService
from app.models.shift_exception import ShiftException
from app.models.whole_shift import WholeShift
from app.repositories.shift_end_repository import ShiftEndRepository
from app.repositories.shift_exception_repository import ShiftExceptionRepository
from app.repositories.shift_start_repository import ShiftStartRepository
from app.repositories.whole_shift_repository import WholeShiftRepository


class GoogleSheetsRetryService:
    def __init__(self) -> None:
        self.shift_exception_repository = ShiftExceptionRepository()
        self.shift_start_repository = ShiftStartRepository()
        self.shift_end_repository = ShiftEndRepository()
        self.whole_shift_repository = WholeShiftRepository()
        self.start_events_sheet_service = StartEventsSheetService()
        self.end_events_sheet_service = EndEventsSheetService()
        self.whole_shifts_sheet_service = WholeShiftsSheetService()

    def retry_open_sheet_sync_failures(self, db: Session) -> dict:
        open_failures = self.shift_exception_repository.list_open_sheet_sync_failures(db=db)

        retried_count = 0
        resolved_count = 0
        failed_retries: list[dict] = []

        for failure in open_failures:
            retried_count += 1

            try:
                self._retry_failure(db=db, failure=failure)
                self.shift_exception_repository.mark_as_resolved(
                    db=db,
                    shift_exception=failure,
                )
                resolved_count += 1
            except Exception as exc:
                failed_retries.append(
                    {
                        "exception_id": failure.exception_id,
                        "exception_type": failure.exception_type,
                        "message": str(exc),
                    }
                )

        return {
            "total_open_failures": len(open_failures),
            "retried_count": retried_count,
            "resolved_count": resolved_count,
            "failed_count": len(failed_retries),
            "failed_retries": failed_retries,
        }

    def _retry_failure(self, db: Session, failure: ShiftException) -> None:
        if failure.exception_type == "start_sheet_append_failed":
            if failure.related_start_id is None:
                raise ValueError("Missing related_start_id for start sheet retry")

            shift_start = self.shift_start_repository.get_by_start_id(
                db=db,
                start_id=failure.related_start_id,
            )
            if shift_start is None:
                raise ValueError("Shift start not found for retry")

            self.start_events_sheet_service.append_start_event(shift_start)
            return

        if failure.exception_type == "end_sheet_append_failed":
            if failure.related_end_id is None:
                raise ValueError("Missing related_end_id for end sheet retry")

            shift_end = self.shift_end_repository.get_by_end_id(
                db=db,
                end_id=failure.related_end_id,
            )
            if shift_end is None:
                raise ValueError("Shift end not found for retry")

            self.end_events_sheet_service.append_end_event(shift_end)
            return

        if failure.exception_type == "whole_shift_sheet_append_failed":
            if failure.related_end_id is None:
                raise ValueError("Missing related_end_id for whole shift retry")

            whole_shift = self._get_whole_shift_by_end_id(db=db, end_id=failure.related_end_id)
            if whole_shift is None:
                raise ValueError("Whole shift not found for retry")

            self.whole_shifts_sheet_service.append_whole_shift(whole_shift)
            return

        raise ValueError(f"Unsupported exception type: {failure.exception_type}")

    def _get_whole_shift_by_end_id(self, db: Session, end_id: str) -> WholeShift | None:
        return (
            db.query(WholeShift)
            .filter(WholeShift.end_id == end_id)
            .first()
        )
