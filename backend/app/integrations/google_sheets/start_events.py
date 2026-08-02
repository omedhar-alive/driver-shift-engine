from app.core.config import settings
from app.integrations.google_sheets.client import GoogleSheetsClient
from app.models.shift_start import ShiftStart
from app.schemas.timezone import serialize_cairo_datetime_for_sheets


class StartEventsSheetService:
    def __init__(self) -> None:
        self.client = GoogleSheetsClient()

    def append_start_event(self, shift_start: ShiftStart) -> None:
        worksheet = self.client.spreadsheet.worksheet(
            settings.google_sheets_start_sheet_name
        )

        worksheet.append_row(
            [
                shift_start.start_id,
                shift_start.driver_code,
                shift_start.plate_number,
                serialize_cairo_datetime_for_sheets(shift_start.start_timestamp),
                shift_start.start_dashboard_image,
                shift_start.start_odo_gemini,
                shift_start.start_soc_gemini,
                shift_start.status,
            ]
        )
