import gspread
from google.oauth2.service_account import Credentials

from app.core.config import settings


class GoogleSheetsClient:
    def __init__(self) -> None:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            settings.google_sheets_credentials_file,
            scopes=scopes,
        )

        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(settings.google_sheets_spreadsheet_id)