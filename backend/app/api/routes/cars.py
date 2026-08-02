from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.car import (
    CarCreate,
    CarRead,
    CarQrValidateRequest,
    CarQrValidateResponse,
)
from app.services.car_service import CarService

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.post("/", response_model=CarRead)
def create_car(
    car_in: CarCreate,
    db: Session = Depends(get_db),
) -> CarRead:
    service = CarService()

    try:
        return service.create_car(db=db, car_in=car_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=list[CarRead])
def list_cars(
    db: Session = Depends(get_db),
) -> list[CarRead]:
    service = CarService()
    return service.list_cars(db=db)


@router.get("/by-id/{car_id}", response_model=CarRead)
def get_car_by_car_id(
    car_id: str,
    db: Session = Depends(get_db),
) -> CarRead:
    service = CarService()
    car = service.get_car_by_car_id(db=db, car_id=car_id)

    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")

    return car


@router.get("/by-plate/{plate_number}", response_model=CarRead)
def get_car_by_plate_number(
    plate_number: str,
    db: Session = Depends(get_db),
) -> CarRead:
    service = CarService()
    car = service.get_car_by_plate_number(db=db, plate_number=plate_number)

    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")

    return car


@router.post("/validate-scan/{plate_number}", response_model=CarRead)
def validate_scanned_plate(
    plate_number: str,
    db: Session = Depends(get_db),
) -> CarRead:
    service = CarService()

    try:
        return service.validate_scanned_plate(db=db, plate_number=plate_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/validate-qr", response_model=CarQrValidateResponse)
def validate_qr(
    payload: CarQrValidateRequest,
    db: Session = Depends(get_db),
) -> CarQrValidateResponse:
    service = CarService()
    result = service.validate_qr_value(db=db, qr_value=payload.qr_value)

    return CarQrValidateResponse(**result)