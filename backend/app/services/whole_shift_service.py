from app.models.shift_end import ShiftEnd
from app.models.shift_start import ShiftStart
from app.models.whole_shift import WholeShift
from app.repositories.whole_shift_repository import WholeShiftRepository
from sqlalchemy.orm import Session


class WholeShiftService:
    def __init__(self) -> None:
        self.repository = WholeShiftRepository()

    def create_whole_shift(
        self,
        db: Session,
        shift_start: ShiftStart,
        shift_end: ShiftEnd,
    ) -> WholeShift:
        start_odo_final = shift_start.start_odo_gemini
        end_odo_final = shift_end.end_odo_gemini
        distance_covered = end_odo_final - start_odo_final

        start_soc_final = shift_start.start_soc_gemini
        end_soc_final = shift_end.end_soc_gemini
        battery_consumed = start_soc_final - end_soc_final

        shift_duration = shift_end.end_timestamp - shift_start.start_timestamp

        electric_consumption = 0.0
        if battery_consumed > 0:
            electric_consumption = distance_covered / battery_consumed

        return self.repository.create(
            db=db,
            start_id=shift_start.start_id,
            end_id=shift_end.end_id,
            driver_code=shift_start.driver_code,
            plate_number=shift_start.plate_number,
            start_dashboard_image=shift_start.start_dashboard_image,
            end_dashboard_image=shift_end.end_dashboard_image,
            start_timestamp=shift_start.start_timestamp,
            end_timestamp=shift_end.end_timestamp,
            start_odo_final=start_odo_final,
            end_odo_final=end_odo_final,
            distance_covered=distance_covered,
            start_soc_final=start_soc_final,
            end_soc_final=end_soc_final,
            battery_consumed=battery_consumed,
            shift_duration=shift_duration,
            electric_consumption=electric_consumption,
        )
