from sqlalchemy.orm import Session

from app.integrations.gemini.ocr import GeminiOCRService
from app.integrations.google_sheets.start_events import StartEventsSheetService
from app.models.shift_start import ShiftStart
from app.repositories.car_repository import CarRepository
from app.repositories.driver_repository import DriverRepository
from app.repositories.shift_start_repository import ShiftStartRepository
from app.schemas.shift_start import ShiftStartCreate
from app.services.errors import OCRRetakeRequiredError
from app.services.shift_exception_service import ShiftExceptionService


class ShiftStartService:
    def __init__(self) -> None:
        self.shift_start_repository = ShiftStartRepository()
        self.driver_repository = DriverRepository()
        self.car_repository = CarRepository()
        self.gemini_ocr_service = GeminiOCRService()
        self.start_events_sheet_service = StartEventsSheetService()
        self.shift_exception_service = ShiftExceptionService()

    def create_shift_start(
        self,
        db: Session,
        driver_code: str,
        shift_start_in: ShiftStartCreate,
    ) -> ShiftStart:
        driver = self.driver_repository.get_by_code(db=db, driver_code=driver_code)
        if driver is None:
            raise ValueError("Driver not found")

        if not driver.active_status:
            raise ValueError("Driver is inactive")

        normalized_plate_number = self._normalize_plate_number(shift_start_in.plate_number)

        existing_open_shift = self.shift_start_repository.get_open_shift_by_driver_code(
            db=db,
            driver_code=driver_code,
        )
        if existing_open_shift is not None:
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="duplicate_start",
                message="Driver already has an open shift",
                driver_code=driver_code,
                plate_number=normalized_plate_number,
                related_start_id=existing_open_shift.start_id,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": normalized_plate_number,
                    "start_dashboard_image": shift_start_in.start_dashboard_image,
                },
            )
            raise ValueError("Driver already has an open shift")

        car = self.car_repository.get_by_plate_number(
            db=db,
            plate_number=normalized_plate_number,
        )
        if car is None:
            raise ValueError("Scanned plate number does not match any car")

        if not car.active_status:
            raise ValueError("Car is inactive")

        gemini_result = self.gemini_ocr_service.extract_dashboard_values(
            image_reference=shift_start_in.start_dashboard_image,
        )

        provider_error_types = {"quota_exhausted", "rate_limited", "provider_unavailable"}
        if gemini_result.get("error_type") in provider_error_types:
            pending_shift_start = self.shift_start_repository.create(
                db=db,
                driver_code=driver_code,
                plate_number=normalized_plate_number,
                start_dashboard_image=shift_start_in.start_dashboard_image,
                ocr_image_data=None,
                ocr_image_mime_type=None,
                retry_image_data=None,
                retry_image_mime_type=None,
                ocr_raw_response=gemini_result.get("raw_response"),
                start_odo_gemini=None,
                start_soc_gemini=None,
                status="pending_ocr_quota",
            )

            self.shift_exception_service.create_exception(
                db=db,
                exception_type="pending_ocr_quota",
                message=gemini_result["message"],
                driver_code=driver_code,
                plate_number=normalized_plate_number,
                related_start_id=pending_shift_start.start_id,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": normalized_plate_number,
                    "start_dashboard_image": shift_start_in.start_dashboard_image,
                    "provider_error_type": gemini_result.get("error_type"),
                },
            )

            return pending_shift_start

        if not gemini_result["success"]:
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="ocr_failed",
                message=gemini_result["message"],
                driver_code=driver_code,
                plate_number=normalized_plate_number,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": normalized_plate_number,
                    "start_dashboard_image": shift_start_in.start_dashboard_image,
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
                plate_number=normalized_plate_number,
                raw_payload={
                    "driver_code": driver_code,
                    "plate_number": normalized_plate_number,
                    "start_dashboard_image": shift_start_in.start_dashboard_image,
                    "gemini_result": gemini_result,
                },
            )
            raise OCRRetakeRequiredError(message)

        shift_start = self.shift_start_repository.create(
            db=db,
            driver_code=driver_code,
            plate_number=normalized_plate_number,
            start_dashboard_image=shift_start_in.start_dashboard_image,
            ocr_image_data=None,
            ocr_image_mime_type=None,
            retry_image_data=None,
            retry_image_mime_type=None,
            ocr_raw_response=gemini_result.get("raw_response"),
            start_odo_gemini=gemini_result["odo"],
            start_soc_gemini=gemini_result["soc"],
            status="accepted",
        )

        try:
            self.start_events_sheet_service.append_start_event(shift_start)
        except Exception as exc:
            print(f"Google Sheets append failed for start event: {exc}")
            self.shift_exception_service.create_exception(
                db=db,
                exception_type="start_sheet_append_failed",
                message=str(exc),
                driver_code=driver_code,
                plate_number=normalized_plate_number,
                related_start_id=shift_start.start_id,
                raw_payload={
                    "start_id": shift_start.start_id,
                    "driver_code": driver_code,
                    "plate_number": normalized_plate_number,
                },
            )

        return shift_start

    def _normalize_plate_number(self, plate_number: str) -> str:
        normalized = " ".join(plate_number.strip().split())
        normalized = normalized.replace("أ", "ا")
        normalized = normalized.replace("ى", "ي")
        return normalized
