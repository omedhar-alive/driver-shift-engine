from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import DateTime, Float, Interval, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WholeShift(Base):
    __tablename__ = "whole_shifts"

    shift_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    start_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    end_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)

    driver_code: Mapped[str] = mapped_column(String(50), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(50), nullable=False)
    start_dashboard_image: Mapped[str] = mapped_column(String(500), nullable=False)
    end_dashboard_image: Mapped[str] = mapped_column(String(500), nullable=False)

    start_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    start_odo_final: Mapped[float] = mapped_column(nullable=False)
    end_odo_final: Mapped[float] = mapped_column(nullable=False)
    distance_covered: Mapped[float] = mapped_column(nullable=False)

    start_soc_final: Mapped[float] = mapped_column(nullable=False)
    end_soc_final: Mapped[float] = mapped_column(nullable=False)
    battery_consumed: Mapped[float] = mapped_column(nullable=False)

    shift_duration: Mapped[timedelta] = mapped_column(Interval, nullable=False)
    electric_consumption: Mapped[float] = mapped_column(nullable=False)
