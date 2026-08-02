from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.models import Driver
from app.db.session import engine


TIMESTAMP_TZ_MIGRATIONS = [
    ("driver_sessions", "created_at"),
    ("driver_sessions", "last_seen_at"),
    ("driver_sessions", "revoked_at"),
    ("shift_starts", "start_timestamp"),
    ("shift_ends", "end_timestamp"),
    ("shift_exceptions", "created_at"),
    ("shift_exceptions", "resolved_at"),
    ("whole_shifts", "start_timestamp"),
    ("whole_shifts", "end_timestamp"),
]

MISSING_COLUMN_MIGRATIONS = [
    ("shift_starts", "ocr_image_data", "TEXT"),
    ("shift_starts", "ocr_image_mime_type", "VARCHAR(100)"),
    ("shift_starts", "retry_image_data", "TEXT"),
    ("shift_starts", "retry_image_mime_type", "VARCHAR(100)"),
    ("shift_starts", "ocr_raw_response", "TEXT"),
    ("shift_ends", "ocr_image_data", "TEXT"),
    ("shift_ends", "ocr_image_mime_type", "VARCHAR(100)"),
    ("shift_ends", "retry_image_data", "TEXT"),
    ("shift_ends", "retry_image_mime_type", "VARCHAR(100)"),
    ("shift_ends", "ocr_raw_response", "TEXT"),
    ("whole_shifts", "start_dashboard_image", "VARCHAR(500)"),
    ("whole_shifts", "end_dashboard_image", "VARCHAR(500)"),
]


def _sync_timestamp_columns_to_timestamptz() -> None:
    inspector = inspect(engine)

    with engine.begin() as connection:
        for table_name, column_name in TIMESTAMP_TZ_MIGRATIONS:
            if not inspector.has_table(table_name):
                continue

            columns = inspector.get_columns(table_name)
            column = next((item for item in columns if item["name"] == column_name), None)

            if column is None:
                continue

            column_type = str(column["type"]).lower()

            if "timestamp with time zone" in column_type or "timestamptz" in column_type:
                continue

            if "timestamp" not in column_type:
                continue

            connection.execute(
                text(
                    f"""
                    ALTER TABLE {table_name}
                    ALTER COLUMN {column_name}
                    TYPE TIMESTAMP WITH TIME ZONE
                    USING {column_name} AT TIME ZONE 'UTC'
                    """
                )
            )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_missing_columns()
    _sync_timestamp_columns_to_timestamptz()


def _ensure_missing_columns() -> None:
    inspector = inspect(engine)

    with engine.begin() as connection:
        for table_name, column_name, column_sql in MISSING_COLUMN_MIGRATIONS:
            if not inspector.has_table(table_name):
                continue

            columns = inspector.get_columns(table_name)
            if any(item["name"] == column_name for item in columns):
                continue

            connection.execute(
                text(
                    f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN {column_name} {column_sql}
                    """
                )
            )
