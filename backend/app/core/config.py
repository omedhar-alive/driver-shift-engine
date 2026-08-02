from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Driver Shift System API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    remember_me_expire_minutes: int

    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: int
    use_vertex_ai: bool = False
    google_cloud_project: Optional[str] = None
    gemini_regions: str = "us-central1,europe-west1"
    google_service_account_json: Optional[str] = None
    google_cloud_storage_bucket_name: Optional[str] = None
    google_cloud_storage_dashboard_images_prefix: str = "dashboard-images"

    google_sheets_credentials_file: str
    google_sheets_spreadsheet_id: str
    google_sheets_start_sheet_name: str
    google_sheets_end_sheet_name: str
    google_sheets_whole_shift_sheet_name: str

    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
