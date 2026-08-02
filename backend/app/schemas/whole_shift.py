from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.timezone import serialize_cairo_datetime


class WholeShiftRead(BaseModel):
    shift_id: str
    start_id: str
    end_id: str
    driver_code: str
    plate_number: str
    start_dashboard_image: str
    end_dashboard_image: str
    start_timestamp: datetime
    end_timestamp: datetime
    start_odo_final: float
    end_odo_final: float
    distance_covered: float
    start_soc_final: float
    end_soc_final: float
    battery_consumed: float
    shift_duration: timedelta
    electric_consumption: float

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("start_timestamp", "end_timestamp", when_used="json")
    def serialize_timestamps(self, value: datetime) -> str:
        return serialize_cairo_datetime(value)
