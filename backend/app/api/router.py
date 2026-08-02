from fastapi import APIRouter

from app.api.routes.cars import router as cars_router
from app.api.routes.db_test import router as db_test_router
from app.api.routes.drivers import router as drivers_router
from app.api.routes.health import router as health_router
from app.api.routes.ocr_images import router as ocr_images_router
from app.api.routes.shift_ends import router as shift_ends_router
from app.api.routes.shift_starts import router as shift_starts_router
from app.api.routes.google_sheets_retry import router as google_sheets_retry_router
from app.api.routes.auth import router as auth_router
from app.api.routes.uploads import router as uploads_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(db_test_router)
api_router.include_router(drivers_router)
api_router.include_router(cars_router)
api_router.include_router(ocr_images_router)
api_router.include_router(shift_starts_router)
api_router.include_router(shift_ends_router)
api_router.include_router(google_sheets_retry_router)
api_router.include_router(auth_router)
api_router.include_router(uploads_router)
