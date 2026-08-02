from sqlalchemy.orm import Session

from app.core.security.password import hash_password, verify_password
from app.models.driver import Driver
from app.repositories.driver_repository import DriverRepository
from app.schemas.driver import DriverCreate, DriverLogin


class DriverService:
    def __init__(self) -> None:
        self.repository = DriverRepository()

    def create_driver(self, db: Session, driver_in: DriverCreate) -> Driver:
        existing_by_code = self.repository.get_by_code(db=db, driver_code=driver_in.driver_code)
        if existing_by_code is not None:
            raise ValueError("Driver code already exists")

        existing_by_phone = self.repository.get_by_phone_number(
            db=db,
            phone_number=driver_in.phone_number,
        )
        if existing_by_phone is not None:
            raise ValueError("Phone number already exists")

        existing_by_email = self.repository.get_by_email(db=db, email=driver_in.email)
        if existing_by_email is not None:
            raise ValueError("Email already exists")

        password_hash = hash_password(driver_in.password)

        return self.repository.create(
            db=db,
            driver_code=driver_in.driver_code,
            driver_name=driver_in.driver_name,
            phone_number=driver_in.phone_number,
            email=driver_in.email,
            password_hash=password_hash,
        )

    def list_drivers(self, db: Session) -> list[Driver]:
        return self.repository.list(db=db)

    def get_driver_by_code(self, db: Session, driver_code: str) -> Driver | None:
        return self.repository.get_by_code(db=db, driver_code=driver_code)

    def authenticate_driver(self, db: Session, login_in: DriverLogin) -> Driver:
        driver = self.repository.get_by_code(db=db, driver_code=login_in.driver_code)

        if driver is None:
            raise ValueError("Invalid driver code or password")

        if not driver.active_status:
            raise ValueError("Driver is inactive")

        if not verify_password(login_in.password, driver.password_hash):
            raise ValueError("Invalid driver code or password")

        return driver