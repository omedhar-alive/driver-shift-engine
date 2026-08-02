from sqlalchemy.orm import Session

from app.models.shift_end import ShiftEnd


class ShiftEndRepository:
    def create(
        self,
        db: Session,
        matched_start_id: str,
        driver_code: str,
        plate_number: str,
        end_dashboard_image: str,
        ocr_image_data: str | None,
        ocr_image_mime_type: str | None,
        retry_image_data: str | None,
        retry_image_mime_type: str | None,
        ocr_raw_response: str | None,
        end_odo_gemini: float | None,
        end_soc_gemini: float | None,
        status: str = "accepted",
    ) -> ShiftEnd:
        shift_end = ShiftEnd(
            matched_start_id=matched_start_id,
            driver_code=driver_code,
            plate_number=plate_number,
            end_dashboard_image=end_dashboard_image,
            ocr_image_data=ocr_image_data,
            ocr_image_mime_type=ocr_image_mime_type,
            retry_image_data=retry_image_data,
            retry_image_mime_type=retry_image_mime_type,
            ocr_raw_response=ocr_raw_response,
            end_odo_gemini=end_odo_gemini,
            end_soc_gemini=end_soc_gemini,
            status=status,
        )
        db.add(shift_end)
        db.commit()
        db.refresh(shift_end)
        return shift_end

    def get_by_end_id(self, db: Session, end_id: str) -> ShiftEnd | None:
        return (
            db.query(ShiftEnd)
            .filter(ShiftEnd.end_id == end_id)
            .first()
        )

    def get_by_matched_start_id(self, db: Session, matched_start_id: str) -> ShiftEnd | None:
        return (
            db.query(ShiftEnd)
            .filter(ShiftEnd.matched_start_id == matched_start_id)
            .order_by(ShiftEnd.end_timestamp.desc())
            .first()
        )

    def get_latest_by_driver_code(self, db: Session, driver_code: str) -> ShiftEnd | None:
        return (
            db.query(ShiftEnd)
            .filter(ShiftEnd.driver_code == driver_code)
            .order_by(ShiftEnd.end_timestamp.desc())
            .first()
        )

    def list_pending_ocr_quota(self, db: Session) -> list[ShiftEnd]:
        return (
            db.query(ShiftEnd)
            .filter(ShiftEnd.status == "pending_ocr_quota")
            .order_by(ShiftEnd.end_timestamp.asc())
            .all()
        )

    def mark_pending_as_accepted(
        self,
        db: Session,
        shift_end: ShiftEnd,
        end_odo_gemini: float,
        end_soc_gemini: float,
        ocr_raw_response: str | None,
    ) -> ShiftEnd:
        shift_end.end_odo_gemini = end_odo_gemini
        shift_end.end_soc_gemini = end_soc_gemini
        shift_end.retry_image_data = None
        shift_end.retry_image_mime_type = None
        shift_end.ocr_raw_response = ocr_raw_response
        shift_end.status = "accepted"
        db.commit()
        db.refresh(shift_end)
        return shift_end

    def mark_pending_as_unrecoverable(
        self,
        db: Session,
        shift_end: ShiftEnd,
    ) -> ShiftEnd:
        shift_end.status = "pending_ocr_failed_unrecoverable"
        db.commit()
        db.refresh(shift_end)
        return shift_end
