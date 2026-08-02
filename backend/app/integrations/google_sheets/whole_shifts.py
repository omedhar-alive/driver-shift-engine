from app.core.config import settings
from app.integrations.google_sheets.client import GoogleSheetsClient
from app.models.whole_shift import WholeShift
from app.schemas.timezone import serialize_cairo_datetime_for_sheets


class WholeShiftsSheetService:
    def __init__(self) -> None:
        self.client = GoogleSheetsClient()

    def append_whole_shift(self, whole_shift: WholeShift) -> None:
        worksheet = self.client.spreadsheet.worksheet(
            settings.google_sheets_whole_shift_sheet_name
        )

        worksheet.append_row(
            [
                whole_shift.shift_id,
                whole_shift.start_id,
                whole_shift.end_id,
                whole_shift.driver_code,
                whole_shift.plate_number,
                serialize_cairo_datetime_for_sheets(whole_shift.start_timestamp),
                serialize_cairo_datetime_for_sheets(whole_shift.end_timestamp),
                whole_shift.start_dashboard_image,
                whole_shift.end_dashboard_image,
                whole_shift.start_odo_final,
                whole_shift.end_odo_final,
                whole_shift.distance_covered,
                whole_shift.start_soc_final,
                whole_shift.end_soc_final,
                whole_shift.battery_consumed,
                str(whole_shift.shift_duration),
                whole_shift.electric_consumption,
            ]
        )
