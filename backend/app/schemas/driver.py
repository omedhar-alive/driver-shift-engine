from typing import Literal

from pydantic import BaseModel, EmailStr, ConfigDict


class DriverCreate(BaseModel):
    driver_code: str
    driver_name: str
    phone_number: str
    email: EmailStr
    password: str


class DriverRead(BaseModel):
    driver_code: str
    driver_name: str
    phone_number: str
    email: EmailStr
    active_status: bool

    model_config = ConfigDict(from_attributes=True)


class DriverLogin(BaseModel):
    driver_code: str
    password: str
    remember_me: bool = False


class DriverLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver: DriverRead


class DriverLandingState(BaseModel):
    flow: Literal["start_shift", "end_shift"]
    route: str
    reason: Literal["no_active_shift", "active_shift"]
    active_shift_id: str | None = None
    active_shift_status: str | None = None
