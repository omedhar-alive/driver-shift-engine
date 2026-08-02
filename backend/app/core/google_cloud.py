import json
import os
from pathlib import Path


def ensure_google_application_credentials(
    service_account_json: str | None,
    fallback_credentials_file: str | None = None,
) -> None:
    existing_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if existing_path and Path(existing_path).exists():
        return

    if fallback_credentials_file:
        fallback_path = Path(fallback_credentials_file)
        if fallback_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(fallback_path)
            return

    if not service_account_json:
        return

    credentials_path = Path("/tmp/gcp-service-account.json")
    parsed_json = json.loads(service_account_json)
    credentials_path.write_text(
        json.dumps(parsed_json),
        encoding="utf-8",
    )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
