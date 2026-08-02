import threading
import time

from app.db.session import SessionLocal
from app.services.google_sheets_retry_service import GoogleSheetsRetryService

RETRY_INTERVAL_SECONDS = 180


def start_google_sheets_retry_worker() -> None:
    thread = threading.Thread(
        target=_run_google_sheets_retry_loop,
        daemon=True,
    )
    thread.start()


def _run_google_sheets_retry_loop() -> None:
    while True:
        db = SessionLocal()
        try:
            service = GoogleSheetsRetryService()
            result = service.retry_open_sheet_sync_failures(db=db)

            if result["retried_count"] > 0:
                print(
                    "Google Sheets retry worker:",
                    f"retried={result['retried_count']},",
                    f"resolved={result['resolved_count']},",
                    f"failed={result['failed_count']}",
                )
        except Exception as exc:
            print(f"Google Sheets retry worker failed: {exc}")
        finally:
            db.close()

        time.sleep(RETRY_INTERVAL_SECONDS)
