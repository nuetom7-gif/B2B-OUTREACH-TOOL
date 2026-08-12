from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.discovery_routes import router as discovery_router
from app.api.routes import router
from app.core.config import get_settings
from app.db.session import engine
from app.models.base import Base
from app.jobs.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
logger = logging.getLogger("yash_outreach.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_failed_requests(request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled backend error: %s %s", request.method, request.url.path)
        raise
    if response.status_code >= 400:
        logger.warning("Backend request failed: %s %s -> %s", request.method, request.url.path, response.status_code)
    return response

app.include_router(router)
app.include_router(discovery_router)
