from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.timezone import serialize_cairo_datetime


class ShiftStartCreate(BaseModel):
    plate_number: str
    start_dashboard_image: str


class ShiftStartRead(BaseModel):
    start_id: str
    driver_code: str
    plate_number: str
    start_timestamp: datetime
    start_dashboard_image: str
    start_odo_gemini: float | None
    start_soc_gemini: float | None
    status: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("start_timestamp", when_used="json")
    def serialize_start_timestamp(self, value: datetime) -> str:
        return serialize_cairo_datetime(value)
