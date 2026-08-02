from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShiftExceptionRead(BaseModel):
    exception_id: str
    exception_type: str
    driver_code: str | None
    plate_number: str | None
    related_start_id: str | None
    related_end_id: str | None
    message: str
    raw_payload: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None

    model_config = ConfigDict(from_attributes=True)
