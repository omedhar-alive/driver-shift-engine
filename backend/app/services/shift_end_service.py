from sqlalchemy.orm import Session

from app.integrations.gemini.ocr import GeminiOCRService
from app.integrations.google_sheets.end_events import EndEventsSheetService
from app.integrations.google_sheets.whole_shifts import WholeShiftsSheetService
from app.models.shift_end import ShiftEnd
from app.repositories.shift_end_repository import ShiftEndRepository
from app.repositories.shift_start_repository import ShiftStartRepository
from app.schemas.shift_end import ShiftEndCreate
from app.services.errors import OCRRetakeRequiredError
from app.services.shift_exception_service import ShiftExceptionService
from app.services.whole_shift_service import WholeShiftService


class ShiftEndService:
    def __init__(self) -> None:
        self.shift_end_repository = ShiftEndRepository()
        self.shift_start_repository = ShiftStartRepository()
        self.gemini_ocr_service = GeminiOCRService()
        self.end_events_sheet_service = EndEventsSheetService()
        self.whole_shift_service = WholeShiftService()
        self.whole_shifts_sheet_service = WholeShiftsSheetService()
        self.shift_exception_service = ShiftExceptionService()

    @staticmethod
    def _mark_as_already_processed(shift_end: ShiftEnd) -> ShiftEnd:
        setattr(shift_end, "already_processed", True)
        return shift_end

    def create_shift_end(
        self,
        db: Session,
        driver_code: str,
        shift_end_in: ShiftEndCreate,
    ) -> ShiftEnd:
        open_shift = self.shift_start_repository.get_open_shift_by_driver_code(
            db=db,
            driver_code=driver_code,
        )
        if open_shift is None:
            latest_start = self.shift_start_repository.get_latest_by_driver_code(
                db=db,
                driver_code=driver_code,
            )
            if latest_start is not None and latest_start.status == "closed":
                existing_shift_end = self.shift_end_repository.get_by_matched_start_id(
                    db=db,
                    matched_start_id=latest_start.start_id,
                )
                if existing_shift_end is not None:
                    return self._mark_as_already_processed(existing_shift_end)

            self.shift_exception_service.create_exception(
                db=db,
                exception_type="end_without_open_start",
                message="Driver does not have an open shift",
                driver_code=driver_code,
                raw_payload={
                    "driver_code": driver_code,
                    "end_dashboard_image": shift_end_in.end_dashboard_image,
                },
            )
            raise ValueError("Driver does not have an open shift")

        existing_shift_end = self.shift_end_repository.get_by_matched_start_id(
            db=db,
            matched_start_id=open_shift.start_id,
        )
        if existing_shift_end is not None:
            return self._mark_as_already_processed(existing_shift_end)

        gemini_result = self.gemini_ocr_service.extract_dashboard_values(
            image_reference=shift_end_in.end_dashboard_image,
        )

        provider_error_types = {"quota_exhausted", "rate_limited", "provider_unavailable"}
        if gemini_result.get("error_type") in provider_error_types:
            pending_shift_end = self.shift_end_repository.create(
                db=db,
                matched_start_id=open_shift.start_id,
                driver_code=driver_code,
                plate_number=open_shift.plate_number,
                end_dashboard_image=shift_end_in.end_dashboard_image,
                ocr_image_data=None,
                ocr_image_mime_type=None,
                retry_image_data=None,
                retry_image_mime_type=None,
                ocr_raw_response=gemini_result.get("raw_response"),
                end_odo_gemini=None,
                end_soc_gemini=None,
                status="pending_ocr_quota",
            )

            self.shift_start_repository.mark_as_closed(db=db, start_id=open_shift.start_id)

            self.shift_exception_service.create_exception(
                db=db,
                exception_type="pending_ocr_quota",
                message=gemini_result["message"],
                driver_code=driver_code,
                plate_number=open_shift.plate_number,
                related_start_id=open_shift.start_id,
                related_end_id=pending_shift_end.end_id,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": open_shift.plate_number,
                    "end_dashboard_image": shift_end_in.end_dashboard_image,
                    "provider_error_type": gemini_result.get("error_type"),
                },
            )

            return pending_shift_end

        if not gemini_result["success"]:
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="ocr_failed",
                message=gemini_result["message"],
                driver_code=driver_code,
                plate_number=open_shift.plate_number,
                related_start_id=open_shift.start_id,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": open_shift.plate_number,
                    "end_dashboard_image": shift_end_in.end_dashboard_image,
                    "gemini_result": gemini_result,
                },
            )
            if gemini_result.get("requires_retake"):
                raise OCRRetakeRequiredError(gemini_result["message"])
            raise ValueError(gemini_result["message"])

        if gemini_result["odo_confidence"] < 0.85 or gemini_result["soc_confidence"] < 0.85:
            message = "الصورة غير واضحة بما يكفي. يرجى التقاط صورة أوضح للتابلوه ثم المحاولة مرة أخرى."
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="ocr_low_confidence",
                message=message,
                driver_code=driver_code,
                plate_number=open_shift.plate_number,
                related_start_id=open_shift.start_id,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": open_shift.plate_number,
                    "end_dashboard_image": shift_end_in.end_dashboard_image,
                    "gemini_result": gemini_result,
                },
            )
            raise OCRRetakeRequiredError(message)

        shift_end = self.shift_end_repository.create(
            db=db,
            matched_start_id=open_shift.start_id,
            driver_code=driver_code,
            plate_number=open_shift.plate_number,
            end_dashboard_image=shift_end_in.end_dashboard_image,
            ocr_image_data=None,
            ocr_image_mime_type=None,
            retry_image_data=None,
            retry_image_mime_type=None,
            ocr_raw_response=gemini_result.get("raw_response"),
            end_odo_gemini=gemini_result["odo"],
            end_soc_gemini=gemini_result["soc"],
            status="accepted",
        )

        self.shift_start_repository.mark_as_closed(db=db, start_id=open_shift.start_id)

        whole_shift = self.whole_shift_service.create_whole_shift(
            db=db,
            shift_start=open_shift,
            shift_end=shift_end,
        )

        try:
            self.whole_shifts_sheet_service.append_whole_shift(whole_shift)
        except Exception as exc:
            print(f"Google Sheets append failed for whole shift: {exc}")
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="whole_shift_sheet_append_failed",
                message=str(exc),
                driver_code=driver_code,
                plate_number=open_shift.plate_number,
                related_start_id=open_shift.start_id,
                related_end_id=shift_end.end_id,
                raw_payload={
                    "shift_id": whole_shift.shift_id,
                    "start_id": open_shift.start_id,
                    "end_id": shift_end.end_id,
                },
            )

        try:
            self.end_events_sheet_service.append_end_event(shift_end)
        except Exception as exc:
            print(f"Google Sheets append failed for end event: {exc}")
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="end_sheet_append_failed",
                message=str(exc),
                driver_code=driver_code,
                plate_number=open_shift.plate_number,
                related_start_id=open_shift.start_id,
                related_end_id=shift_end.end_id,
                raw_payload={
                    "end_id": shift_end.end_id,
                    "start_id": open_shift.start_id,
                    "driver_code": driver_code,
                },
            )

        return shift_end

    def get_latest_shift_end(
        self,
        db: Session,
        driver_code: str,
    ) -> ShiftEnd | None:
        return self.shift_end_repository.get_latest_by_driver_code(
            db=db,
            driver_code=driver_code,
        )
