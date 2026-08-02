from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.workers.google_sheets_retry_worker import start_google_sheets_retry_worker
from app.workers.pending_ocr_retry_worker import start_pending_ocr_retry_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_google_sheets_retry_worker()
    start_pending_ocr_retry_worker()
    yield

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_application()
