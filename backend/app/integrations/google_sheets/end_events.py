from app.core.config import settings
from app.integrations.google_sheets.client import GoogleSheetsClient
from app.models.shift_end import ShiftEnd
from app.schemas.timezone import serialize_cairo_datetime_for_sheets


class EndEventsSheetService:
    def __init__(self) -> None:
        self.client = GoogleSheetsClient()

    def append_end_event(self, shift_end: ShiftEnd) -> None:
        worksheet = self.client.spreadsheet.worksheet(
            settings.google_sheets_end_sheet_name
        )

        worksheet.append_row(
            [
                shift_end.end_id,
                shift_end.matched_start_id,
                shift_end.driver_code,
                shift_end.plate_number,
                serialize_cairo_datetime_for_sheets(shift_end.end_timestamp),
                shift_end.end_dashboard_image,
                shift_end.end_odo_gemini,
                shift_end.end_soc_gemini,
                shift_end.status,
            ]
        )
