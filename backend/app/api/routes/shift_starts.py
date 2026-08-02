from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_driver
from app.api.dependencies import get_db
from app.models.driver import Driver
from app.schemas.shift_start import ShiftStartCreate, ShiftStartRead
from app.services.errors import OCRRetakeRequiredError
from app.services.shift_start_service import ShiftStartService

router = APIRouter(prefix="/shift-starts", tags=["Shift Starts"])


@router.post("/", response_model=ShiftStartRead)
def create_shift_start(
    shift_start_in: ShiftStartCreate,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> ShiftStartRead:
    service = ShiftStartService()

    try:
        return service.create_shift_start(
            db=db,
            driver_code=current_driver.driver_code,
            shift_start_in=shift_start_in,
        )
    except OCRRetakeRequiredError as exc:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "requires_retake": True},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/open", response_model=ShiftStartRead | None)
def get_open_shift(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> ShiftStartRead | None:
    service = ShiftStartService()
    return service.shift_start_repository.get_open_shift_by_driver_code(
        db=db,
        driver_code=current_driver.driver_code,
    )
