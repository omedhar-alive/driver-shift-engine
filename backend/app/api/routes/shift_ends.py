from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_driver
from app.api.dependencies import get_db
from app.models.driver import Driver
from app.schemas.shift_end import ShiftEndCreate, ShiftEndRead
from app.services.errors import OCRRetakeRequiredError
from app.services.shift_end_service import ShiftEndService

router = APIRouter(prefix="/shift-ends", tags=["Shift Ends"])


@router.post("/", response_model=ShiftEndRead)
def create_shift_end(
    shift_end_in: ShiftEndCreate,
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> ShiftEndRead:
    service = ShiftEndService()

    try:
        return service.create_shift_end(
            db=db,
            driver_code=current_driver.driver_code,
            shift_end_in=shift_end_in,
        )
    except OCRRetakeRequiredError as exc:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "requires_retake": True},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/latest", response_model=ShiftEndRead | None)
def get_latest_shift_end(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> ShiftEndRead | None:
    service = ShiftEndService()
    return service.get_latest_shift_end(
        db=db,
        driver_code=current_driver.driver_code,
    )
