from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Car(Base):
    __tablename__ = "cars"

    car_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    qr_value: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    active_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)