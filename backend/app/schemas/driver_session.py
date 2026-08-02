from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DriverSessionRead(BaseModel):
    session_id: str
    driver_code: str
    status: str
    created_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
