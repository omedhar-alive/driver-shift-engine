from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.models.driver_session import DriverSession


class DriverSessionRepository:
    def create(
        self,
        db: Session,
        driver_code: str,
        status: str = "active",
    ) -> DriverSession:
        driver_session = DriverSession(
            driver_code=driver_code,
            status=status,
        )
        db.add(driver_session)
        db.commit()
        db.refresh(driver_session)
        return driver_session

    def get_by_session_id(self, db: Session, session_id: str) -> DriverSession | None:
        return (
            db.query(DriverSession)
            .filter(DriverSession.session_id == session_id)
            .first()
        )

    def update_last_seen(self, db: Session, driver_session: DriverSession) -> DriverSession:
        driver_session.last_seen_at = datetime.now(UTC)
        db.commit()
        db.refresh(driver_session)
        return driver_session

    def revoke(self, db: Session, driver_session: DriverSession) -> DriverSession:
        driver_session.status = "revoked"
        driver_session.revoked_at = datetime.now(UTC)
        db.commit()
        db.refresh(driver_session)
        return driver_session