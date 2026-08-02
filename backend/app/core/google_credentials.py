import json
from pathlib import Path

from app.core.config import settings


def ensure_google_credentials_file() -> None:
    credentials_json = settings.google_sheets_credentials_json
    credentials_file = Path(settings.google_sheets_credentials_file)

    credentials_file.parent.mkdir(parents=True, exist_ok=True)
    credentials_file.write_text(
        json.dumps(json.loads(credentials_json)),
        encoding="utf-8",
    )