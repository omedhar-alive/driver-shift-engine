from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ShiftEnd(Base):
    __tablename__ = "shift_ends"

    end_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    matched_start_id: Mapped[str] = mapped_column(String(36), nullable=False)
    driver_code: Mapped[str] = mapped_column(String(50), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(50), nullable=False)
    end_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    end_dashboard_image: Mapped[str] = mapped_column(String(500), nullable=False)
    ocr_image_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_image_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retry_image_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_image_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ocr_raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    end_odo_gemini: Mapped[float | None] = mapped_column(nullable=True)
    end_soc_gemini: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="accepted")
