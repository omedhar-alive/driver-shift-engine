from pydantic import BaseModel, ConfigDict


class CarCreate(BaseModel):
    car_id: str
    plate_number: str
    qr_value: str | None = None


class CarRead(BaseModel):
    car_id: str
    plate_number: str
    qr_value: str | None = None
    active_status: bool

    model_config = ConfigDict(from_attributes=True)


class CarQrValidateRequest(BaseModel):
    qr_value: str


class CarQrValidateResponse(BaseModel):
    is_valid: bool
    car_id: str | None = None
    plate_number: str | None = None
    message: str | None = None