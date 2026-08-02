from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.auth.token import create_access_token
from app.schemas.driver import DriverCreate, DriverLogin, DriverLoginResponse, DriverRead
from app.services.driver_service import DriverService
from app.services.driver_session_service import DriverSessionService

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post("/", response_model=DriverRead)
def create_driver(
    driver_in: DriverCreate,
    db: Session = Depends(get_db),
) -> DriverRead:
    service = DriverService()

    try:
        return service.create_driver(db=db, driver_in=driver_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=DriverLoginResponse)
def login_driver(
    login_in: DriverLogin,
    db: Session = Depends(get_db),
) -> DriverLoginResponse:
    driver_service = DriverService()
    session_service = DriverSessionService()

    try:
        driver = driver_service.authenticate_driver(db=db, login_in=login_in)
        driver_session = session_service.create_session(
            db=db,
            driver_code=driver.driver_code,
        )

        access_token = create_access_token(
            driver_code=driver.driver_code,
            session_id=driver_session.session_id,
            remember_me=login_in.remember_me,
        )

        return DriverLoginResponse(
            access_token=access_token,
            driver=driver,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=list[DriverRead])
def list_drivers(
    db: Session = Depends(get_db),
) -> list[DriverRead]:
    service = DriverService()
    return service.list_drivers(db=db)


@router.get("/{driver_code}", response_model=DriverRead)
def get_driver_by_code(
    driver_code: str,
    db: Session = Depends(get_db),
) -> DriverRead:
    service = DriverService()
    driver = service.get_driver_by_code(db=db, driver_code=driver_code)

    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    return driver