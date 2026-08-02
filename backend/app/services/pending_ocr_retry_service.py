import base64

from sqlalchemy.orm import Session

from app.integrations.gemini.ocr import GeminiOCRService
from app.integrations.google_cloud_storage import GoogleCloudStorageService
from app.integrations.google_sheets.end_events import EndEventsSheetService
from app.integrations.google_sheets.start_events import StartEventsSheetService
from app.integrations.google_sheets.whole_shifts import WholeShiftsSheetService
from app.repositories.shift_end_repository import ShiftEndRepository
from app.repositories.shift_exception_repository import ShiftExceptionRepository
from app.repositories.shift_start_repository import ShiftStartRepository
from app.services.whole_shift_service import WholeShiftService


class PendingOCRRetryService:
    def __init__(self) -> None:
        self.gemini_ocr_service = GeminiOCRService()
        self.storage_service = GoogleCloudStorageService()
        self.shift_start_repository = ShiftStartRepository()
        self.shift_end_repository = ShiftEndRepository()
        self.shift_exception_repository = ShiftExceptionRepository()

        self.start_events_sheet_service = StartEventsSheetService()
        self.end_events_sheet_service = EndEventsSheetService()
        self.whole_shifts_sheet_service = WholeShiftsSheetService()
        self.whole_shift_service = WholeShiftService()

    def retry_pending_ocr(self, db: Session) -> dict:
        retried = 0
        resolved = 0
        failed = 0

        pending_starts = self.shift_start_repository.list_pending_ocr_quota(db=db)
        pending_ends = self.shift_end_repository.list_pending_ocr_quota(db=db)

        for shift_start in pending_starts:
            retried += 1
            image_bytes, mime_type = self._load_retry_image(
                image_reference=shift_start.start_dashboard_image,
                encoded_image=shift_start.retry_image_data,
                mime_type=shift_start.retry_image_mime_type,
            )

            if image_bytes is None or mime_type is None:
                self.shift_start_repository.mark_pending_as_unrecoverable(
                    db=db,
                    shift_start=shift_start,
                )
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="pending_ocr_image_missing",
                    message="Pending OCR retry skipped because no usable dashboard image was available.",
                    driver_code=shift_start.driver_code,
                    plate_number=shift_start.plate_number,
                    related_start_id=shift_start.start_id,
                    status="open",
                )
                failed += 1
                continue

            gemini_result = self.gemini_ocr_service.extract_dashboard_values_from_bytes(
                image_bytes=image_bytes,
                mime_type=mime_type,
            )

            provider_error_types = {"quota_exhausted", "rate_limited", "provider_unavailable"}
            if gemini_result.get("error_type") in provider_error_types:
                failed += 1
                continue

            if not gemini_result["success"]:
                self.shift_start_repository.mark_pending_as_unrecoverable(
                    db=db,
                    shift_start=shift_start,
                )
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="ocr_failed",
                    message=gemini_result["message"],
                    driver_code=shift_start.driver_code,
                    plate_number=shift_start.plate_number,
                    related_start_id=shift_start.start_id,
                    status="open",
                )
                failed += 1
                continue

            if gemini_result["odo_confidence"] < 0.85 or gemini_result["soc_confidence"] < 0.85:
                self.shift_start_repository.mark_pending_as_unrecoverable(
                    db=db,
                    shift_start=shift_start,
                )
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="ocr_low_confidence",
                    message="OCR confidence is too low during pending OCR retry.",
                    driver_code=shift_start.driver_code,
                    plate_number=shift_start.plate_number,
                    related_start_id=shift_start.start_id,
                    status="open",
                )
                failed += 1
                continue

            accepted_start = self.shift_start_repository.mark_pending_as_accepted(
                db=db,
                shift_start=shift_start,
                start_odo_gemini=gemini_result["odo"],
                start_soc_gemini=gemini_result["soc"],
                ocr_raw_response=gemini_result.get("raw_response"),
            )

            try:
                self.start_events_sheet_service.append_start_event(accepted_start)
            except Exception as exc:
                print(f"Google Sheets append failed for recovered start event: {exc}")
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="start_sheet_append_failed",
                    message=str(exc),
                    driver_code=accepted_start.driver_code,
                    plate_number=accepted_start.plate_number,
                    related_start_id=accepted_start.start_id,
                    status="open",
                )

            resolved += 1

        for shift_end in pending_ends:
            retried += 1
            image_bytes, mime_type = self._load_retry_image(
                image_reference=shift_end.end_dashboard_image,
                encoded_image=shift_end.retry_image_data,
                mime_type=shift_end.retry_image_mime_type,
            )

            if image_bytes is None or mime_type is None:
                self.shift_end_repository.mark_pending_as_unrecoverable(
                    db=db,
                    shift_end=shift_end,
                )
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="pending_ocr_image_missing",
                    message="Pending OCR retry skipped because no usable dashboard image was available.",
                    driver_code=shift_end.driver_code,
                    plate_number=shift_end.plate_number,
                    related_end_id=shift_end.end_id,
                    status="open",
                )
                failed += 1
                continue

            gemini_result = self.gemini_ocr_service.extract_dashboard_values_from_bytes(
                image_bytes=image_bytes,
                mime_type=mime_type,
            )

            provider_error_types = {"quota_exhausted", "rate_limited", "provider_unavailable"}
            if gemini_result.get("error_type") in provider_error_types:
                failed += 1
                continue

            if not gemini_result["success"]:
                self.shift_end_repository.mark_pending_as_unrecoverable(
                    db=db,
                    shift_end=shift_end,
                )
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="ocr_failed",
                    message=gemini_result["message"],
                    driver_code=shift_end.driver_code,
                    plate_number=shift_end.plate_number,
                    related_end_id=shift_end.end_id,
                    status="open",
                )
                failed += 1
                continue

            if gemini_result["odo_confidence"] < 0.85 or gemini_result["soc_confidence"] < 0.85:
                self.shift_end_repository.mark_pending_as_unrecoverable(
                    db=db,
                    shift_end=shift_end,
                )
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="ocr_low_confidence",
                    message="OCR confidence is too low during pending OCR retry.",
                    driver_code=shift_end.driver_code,
                    plate_number=shift_end.plate_number,
                    related_end_id=shift_end.end_id,
                    status="open",
                )
                failed += 1
                continue

            accepted_end = self.shift_end_repository.mark_pending_as_accepted(
                db=db,
                shift_end=shift_end,
                end_odo_gemini=gemini_result["odo"],
                end_soc_gemini=gemini_result["soc"],
                ocr_raw_response=gemini_result.get("raw_response"),
            )

            matched_start = self.shift_start_repository.get_by_start_id(
                db=db,
                start_id=accepted_end.matched_start_id,
            )

            if matched_start is None:
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="end_without_open_start",
                    message="Recovered pending end could not find its matched start.",
                    driver_code=accepted_end.driver_code,
                    plate_number=accepted_end.plate_number,
                    related_end_id=accepted_end.end_id,
                    status="open",
                )
                failed += 1
                continue

            whole_shift = self.whole_shift_service.create_whole_shift(
                db=db,
                shift_start=matched_start,
                shift_end=accepted_end,
            )

            try:
                self.end_events_sheet_service.append_end_event(accepted_end)
            except Exception as exc:
                print(f"Google Sheets append failed for recovered end event: {exc}")
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="end_sheet_append_failed",
                    message=str(exc),
                    driver_code=accepted_end.driver_code,
                    plate_number=accepted_end.plate_number,
                    related_start_id=matched_start.start_id,
                    related_end_id=accepted_end.end_id,
                    status="open",
                )

            try:
                self.whole_shifts_sheet_service.append_whole_shift(whole_shift)
            except Exception as exc:
                print(f"Google Sheets append failed for recovered whole shift: {exc}")
                self.shift_exception_repository.create(
                    db=db,
                    exception_type="whole_shift_sheet_append_failed",
                    message=str(exc),
                    driver_code=accepted_end.driver_code,
                    plate_number=accepted_end.plate_number,
                    related_start_id=matched_start.start_id,
                    related_end_id=accepted_end.end_id,
                    raw_payload={
                        "shift_id": whole_shift.shift_id,
                        "start_id": matched_start.start_id,
                        "end_id": accepted_end.end_id,
                    },
                    status="open",
                )

            resolved += 1

        return {
            "retried": retried,
            "resolved": resolved,
            "failed": failed,
        }

    def _load_retry_image(
        self,
        image_reference: str,
        encoded_image: str | None,
        mime_type: str | None,
    ) -> tuple[bytes | None, str | None]:
        stored_image = self.storage_service.load_image(image_reference)
        if stored_image is not None:
            return stored_image.content, stored_image.mime_type

        if encoded_image and mime_type:
            try:
                return base64.b64decode(encoded_image), mime_type
            except Exception:
                return None, None

        return None, None
