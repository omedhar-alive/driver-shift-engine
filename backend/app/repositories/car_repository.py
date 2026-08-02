from sqlalchemy.orm import Session

from app.models.car import Car


class CarRepository:
    def create(
        self,
        db: Session,
        car_id: str,
        plate_number: str,
        qr_value: str | None = None,
    ) -> Car:
        car = Car(
            car_id=car_id,
            plate_number=plate_number,
            qr_value=qr_value,
        )
        db.add(car)
        db.commit()
        db.refresh(car)
        return car

    def list(self, db: Session) -> list[Car]:
        return db.query(Car).all()

    def get_by_car_id(self, db: Session, car_id: str) -> Car | None:
        return db.query(Car).filter(Car.car_id == car_id).first()

    def get_by_plate_number(self, db: Session, plate_number: str) -> Car | None:
        return db.query(Car).filter(Car.plate_number == plate_number).first()

    def get_by_qr_value(self, db: Session, qr_value: str) -> Car | None:
        return db.query(Car).filter(Car.qr_value == qr_value).first()