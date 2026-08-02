import threading
import time

from app.db.session import SessionLocal
from app.services.pending_ocr_retry_service import PendingOCRRetryService

RETRY_INTERVAL_SECONDS = 300


def start_pending_ocr_retry_worker() -> None:
    thread = threading.Thread(
        target=_run_pending_ocr_retry_loop,
        daemon=True,
    )
    thread.start()


def _run_pending_ocr_retry_loop() -> None:
    while True:
        db = SessionLocal()
        try:
            service = PendingOCRRetryService()
            result = service.retry_pending_ocr(db=db)

            if result["retried"] > 0:
                print(
                    "Pending OCR retry worker:",
                    f"retried={result['retried']},",
                    f"resolved={result['resolved']},",
                    f"failed={result['failed']}",
                )
        except Exception as exc:
            print(f"Pending OCR retry worker failed: {exc}")
        finally:
            db.close()

        time.sleep(RETRY_INTERVAL_SECONDS)
