from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.timezone import serialize_cairo_datetime


class ShiftEndCreate(BaseModel):
    end_dashboard_image: str


class ShiftEndRead(BaseModel):
    end_id: str
    matched_start_id: str
    driver_code: str
    plate_number: str
    end_timestamp: datetime
    end_dashboard_image: str
    end_odo_gemini: float | None
    end_soc_gemini: float | None
    status: str
    already_processed: bool = False

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("end_timestamp", when_used="json")
    def serialize_end_timestamp(self, value: datetime) -> str:
        return serialize_cairo_datetime(value)
