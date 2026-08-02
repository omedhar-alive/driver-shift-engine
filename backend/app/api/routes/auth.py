from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_driver
from app.api.dependencies import get_db
from app.models.driver import Driver
from app.schemas.driver import DriverLandingState, DriverRead
from app.services.shift_start_service import ShiftStartService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=DriverRead)
def get_me(
    current_driver: Driver = Depends(get_current_driver),
) -> DriverRead:
    return current_driver


@router.get("/landing-state", response_model=DriverLandingState)
def get_landing_state(
    current_driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db),
) -> DriverLandingState:
    shift_start_service = ShiftStartService()
    active_shift = shift_start_service.shift_start_repository.get_open_shift_by_driver_code(
        db=db,
        driver_code=current_driver.driver_code,
    )

    if active_shift is not None:
        return DriverLandingState(
            flow="end_shift",
            route="/end-shift",
            reason="active_shift",
            active_shift_id=active_shift.start_id,
            active_shift_status=active_shift.status,
        )

    return DriverLandingState(
        flow="start_shift",
        route="/start-shift",
        reason="no_active_shift",
    )
