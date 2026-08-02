from sqlalchemy.orm import Session

from app.models.driver import Driver


class DriverRepository:
    def create(
        self,
        db: Session,
        driver_code: str,
        driver_name: str,
        phone_number: str,
        email: str,
        password_hash: str,
    ) -> Driver:
        driver = Driver(
            driver_code=driver_code,
            driver_name=driver_name,
            phone_number=phone_number,
            email=email,
            password_hash=password_hash,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        return driver

    def list(self, db: Session) -> list[Driver]:
        return db.query(Driver).all()

    def get_by_code(self, db: Session, driver_code: str) -> Driver | None:
        return db.query(Driver).filter(Driver.driver_code == driver_code).first()

    def get_by_phone_number(self, db: Session, phone_number: str) -> Driver | None:
        return db.query(Driver).filter(Driver.phone_number == phone_number).first()

    def get_by_email(self, db: Session, email: str) -> Driver | None:
        return db.query(Driver).filter(Driver.email == email).first()