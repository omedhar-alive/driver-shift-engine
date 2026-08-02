from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ShiftException(Base):
    __tablename__ = "shift_exceptions"

    exception_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    exception_type: Mapped[str] = mapped_column(String(100), nullable=False)
    driver_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plate_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_start_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    related_end_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
