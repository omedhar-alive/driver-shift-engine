from sqlalchemy.orm import Session

from app.models.shift_start import ShiftStart


class ShiftStartRepository:
    ACTIVE_SHIFT_STATUSES = (
        "accepted",
        "pending_ocr_quota",
    )

    def create(
        self,
        db: Session,
        driver_code: str,
        plate_number: str,
        start_dashboard_image: str,
        ocr_image_data: str | None,
        ocr_image_mime_type: str | None,
        retry_image_data: str | None,
        retry_image_mime_type: str | None,
        ocr_raw_response: str | None,
        start_odo_gemini: float | None,
        start_soc_gemini: float | None,
        status: str = "accepted",
    ) -> ShiftStart:
        shift_start = ShiftStart(
            driver_code=driver_code,
            plate_number=plate_number,
            start_dashboard_image=start_dashboard_image,
            ocr_image_data=ocr_image_data,
            ocr_image_mime_type=ocr_image_mime_type,
            retry_image_data=retry_image_data,
            retry_image_mime_type=retry_image_mime_type,
            ocr_raw_response=ocr_raw_response,
            start_odo_gemini=start_odo_gemini,
            start_soc_gemini=start_soc_gemini,
            status=status,
        )
        db.add(shift_start)
        db.commit()
        db.refresh(shift_start)
        return shift_start

    def get_open_shift_by_driver_code(self, db: Session, driver_code: str) -> ShiftStart | None:
        return (
            db.query(ShiftStart)
            .filter(
                ShiftStart.driver_code == driver_code,
                ShiftStart.status.in_(self.ACTIVE_SHIFT_STATUSES),
            )
            .first()
        )

    def get_by_start_id(self, db: Session, start_id: str) -> ShiftStart | None:
        return (
            db.query(ShiftStart)
            .filter(ShiftStart.start_id == start_id)
            .first()
        )

    def get_latest_by_driver_code(self, db: Session, driver_code: str) -> ShiftStart | None:
        return (
            db.query(ShiftStart)
            .filter(ShiftStart.driver_code == driver_code)
            .order_by(ShiftStart.start_timestamp.desc())
            .first()
        )

    def list_pending_ocr_quota(self, db: Session) -> list[ShiftStart]:
        return (
            db.query(ShiftStart)
            .filter(ShiftStart.status == "pending_ocr_quota")
            .order_by(ShiftStart.start_timestamp.asc())
            .all()
        )

    def mark_as_closed(self, db: Session, start_id: str) -> ShiftStart:
        shift_start = (
            db.query(ShiftStart)
            .filter(ShiftStart.start_id == start_id)
            .first()
        )

        if shift_start is None:
            raise ValueError("Shift start not found")

        shift_start.status = "closed"
        db.commit()
        db.refresh(shift_start)
        return shift_start

    def mark_pending_as_accepted(
        self,
        db: Session,
        shift_start: ShiftStart,
        start_odo_gemini: float,
        start_soc_gemini: float,
        ocr_raw_response: str | None,
    ) -> ShiftStart:
        shift_start.start_odo_gemini = start_odo_gemini
        shift_start.start_soc_gemini = start_soc_gemini
        shift_start.retry_image_data = None
        shift_start.retry_image_mime_type = None
        shift_start.ocr_raw_response = ocr_raw_response
        shift_start.status = "accepted"
        db.commit()
        db.refresh(shift_start)
        return shift_start

    def mark_pending_as_unrecoverable(
        self,
        db: Session,
        shift_start: ShiftStart,
    ) -> ShiftStart:
        shift_start.status = "pending_ocr_failed_unrecoverable"
        db.commit()
        db.refresh(shift_start)
        return shift_start
