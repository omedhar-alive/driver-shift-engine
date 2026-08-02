from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.whole_shift import WholeShift


class WholeShiftRepository:
    def create(
        self,
        db: Session,
        start_id: str,
        end_id: str,
        driver_code: str,
        plate_number: str,
        start_dashboard_image: str,
        end_dashboard_image: str,
        start_timestamp: datetime,
        end_timestamp: datetime,
        start_odo_final: float,
        end_odo_final: float,
        distance_covered: float,
        start_soc_final: float,
        end_soc_final: float,
        battery_consumed: float,
        shift_duration: timedelta,
        electric_consumption: float,
    ) -> WholeShift:
        whole_shift = WholeShift(
            start_id=start_id,
            end_id=end_id,
            driver_code=driver_code,
            plate_number=plate_number,
            start_dashboard_image=start_dashboard_image,
            end_dashboard_image=end_dashboard_image,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            start_odo_final=start_odo_final,
            end_odo_final=end_odo_final,
            distance_covered=distance_covered,
            start_soc_final=start_soc_final,
            end_soc_final=end_soc_final,
            battery_consumed=battery_consumed,
            shift_duration=shift_duration,
            electric_consumption=electric_consumption,
        )
        db.add(whole_shift)
        db.commit()
        db.refresh(whole_shift)
        return whole_shift

    def get_by_shift_id(self, db: Session, shift_id: str) -> WholeShift | None:
        return (
            db.query(WholeShift)
            .filter(WholeShift.shift_id == shift_id)
            .first()
        )
