from sqlalchemy.orm import Session

from app.models.driver_session import DriverSession
from app.repositories.driver_session_repository import DriverSessionRepository


class DriverSessionService:
    def __init__(self) -> None:
        self.repository = DriverSessionRepository()

    def create_session(self, db: Session, driver_code: str) -> DriverSession:
        return self.repository.create(db=db, driver_code=driver_code)

    def get_active_session(self, db: Session, session_id: str) -> DriverSession | None:
        driver_session = self.repository.get_by_session_id(db=db, session_id=session_id)

        if driver_session is None:
            return None

        if driver_session.status != "active":
            return None

        return driver_session

    def touch_session(self, db: Session, driver_session: DriverSession) -> DriverSession:
        return self.repository.update_last_seen(db=db, driver_session=driver_session)

    def revoke_session(self, db: Session, session_id: str) -> DriverSession | None:
        driver_session = self.repository.get_by_session_id(db=db, session_id=session_id)

        if driver_session is None:
            return None

        return self.repository.revoke(db=db, driver_session=driver_session)