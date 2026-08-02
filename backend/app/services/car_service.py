from sqlalchemy.orm import Session

from app.models.car import Car
from app.repositories.car_repository import CarRepository
from app.schemas.car import CarCreate


class CarService:
    def __init__(self) -> None:
        self.repository = CarRepository()

    def create_car(self, db: Session, car_in: CarCreate) -> Car:
        existing_by_car_id = self.repository.get_by_car_id(
            db=db,
            car_id=car_in.car_id,
        )
        if existing_by_car_id is not None:
            raise ValueError("Car ID already exists")

        existing_by_plate = self.repository.get_by_plate_number(
            db=db,
            plate_number=car_in.plate_number,
        )
        if existing_by_plate is not None:
            raise ValueError("Plate number already exists")

        normalized_qr_value = self._normalize_qr_value(car_in.qr_value)
        if normalized_qr_value is not None:
            existing_by_qr = self.repository.get_by_qr_value(
                db=db,
                qr_value=normalized_qr_value,
            )
            if existing_by_qr is not None:
                raise ValueError("QR value already exists")

        return self.repository.create(
            db=db,
            car_id=car_in.car_id,
            plate_number=car_in.plate_number,
            qr_value=normalized_qr_value,
        )

    def list_cars(self, db: Session) -> list[Car]:
        return self.repository.list(db=db)

    def get_car_by_car_id(self, db: Session, car_id: str) -> Car | None:
        return self.repository.get_by_car_id(db=db, car_id=car_id)

    def get_car_by_plate_number(self, db: Session, plate_number: str) -> Car | None:
        return self.repository.get_by_plate_number(db=db, plate_number=plate_number)

    def validate_scanned_plate(self, db: Session, plate_number: str) -> Car:
        car = self.repository.get_by_plate_number(db=db, plate_number=plate_number)

        if car is None:
            raise ValueError("Scanned plate number does not match any car")

        if not car.active_status:
            raise ValueError("Car is inactive")

        return car

    def validate_qr_value(self, db: Session, qr_value: str) -> dict:
        normalized_qr_value = self._normalize_qr_value(qr_value)
        if normalized_qr_value is None:
            return {
                "is_valid": False,
                "car_id": None,
                "plate_number": None,
                "message": "This car is not registered in the fleet",
            }

        car = self.repository.get_by_qr_value(db=db, qr_value=normalized_qr_value)

        if car is None:
            return {
                "is_valid": False,
                "car_id": None,
                "plate_number": None,
                "message": "This car is not registered in the fleet",
            }

        if not car.active_status:
            return {
                "is_valid": False,
                "car_id": None,
                "plate_number": None,
                "message": "This car is not registered in the fleet",
            }

        return {
            "is_valid": True,
            "car_id": car.car_id,
            "plate_number": car.plate_number,
            "message": None,
        }

    def _normalize_qr_value(self, qr_value: str | None) -> str | None:
        if qr_value is None:
            return None

        normalized = qr_value.strip()
        if not normalized:
            return None

        return normalized