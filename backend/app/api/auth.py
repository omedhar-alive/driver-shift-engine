from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.auth.token import decode_access_token
from app.models.driver import Driver
from app.repositories.driver_repository import DriverRepository
from app.services.driver_session_service import DriverSessionService

security = HTTPBearer()


def get_current_driver(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Driver:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        driver_code = payload.get("sub")
        session_id = payload.get("session_id")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if not driver_code or not session_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    session_service = DriverSessionService()
    driver_session = session_service.get_active_session(db=db, session_id=session_id)

    if driver_session is None:
        raise HTTPException(status_code=401, detail="Session is invalid or revoked")

    session_service.touch_session(db=db, driver_session=driver_session)

    repository = DriverRepository()
    driver = repository.get_by_code(db=db, driver_code=driver_code)

    if driver is None:
        raise HTTPException(status_code=401, detail="Driver not found")

    if not driver.active_status:
        raise HTTPException(status_code=403, detail="Driver is inactive")

    return driver