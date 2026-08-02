from datetime import UTC, datetime
from zoneinfo import ZoneInfo


CAIRO_TZ = ZoneInfo("Africa/Cairo")


def serialize_cairo_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)

    return value.astimezone(CAIRO_TZ).isoformat()


def serialize_cairo_datetime_for_sheets(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)

    return value.astimezone(CAIRO_TZ).replace(tzinfo=None).isoformat()
