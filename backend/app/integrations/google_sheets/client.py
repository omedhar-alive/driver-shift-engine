import gspread
from google.oauth2.service_account import Credentials

from app.core.config import settings


class GoogleSheetsClient:
    """Connects to Google Sheets lazily so a missing/invalid service account
    only breaks Sheets syncing (caught by callers) instead of every endpoint
    that constructs a service depending on this client."""

    def __init__(self) -> None:
        self._client: gspread.Client | None = None
        self._spreadsheet: gspread.Spreadsheet | None = None

    @property
    def client(self) -> gspread.Client:
        if self._client is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            credentials = Credentials.from_service_account_file(
                settings.google_sheets_credentials_file,
                scopes=scopes,
            )

            self._client = gspread.authorize(credentials)

        return self._client

    @property
    def spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            self._spreadsheet = self.client.open_by_key(settings.google_sheets_spreadsheet_id)

        return self._spreadsheet