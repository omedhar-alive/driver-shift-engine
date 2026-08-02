from app.core.security.password import hash_password
from app.db.session import SessionLocal
from app.repositories.driver_repository import DriverRepository

DEMO_DRIVER_CODE = "User"
DEMO_DRIVER_PASSWORD = "123456"


def seed_demo_driver() -> None:
    db = SessionLocal()
    try:
        repository = DriverRepository()
        if repository.get_by_code(db=db, driver_code=DEMO_DRIVER_CODE) is not None:
            return

        repository.create(
            db=db,
            driver_code=DEMO_DRIVER_CODE,
            driver_name="User",
            phone_number="0000000000",
            email="demo.user@shiftengine.app",
            password_hash=hash_password(DEMO_DRIVER_PASSWORD),
        )
    finally:
        db.close()
