from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Driver(Base):
    __tablename__ = "drivers"

    driver_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    driver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    active_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)