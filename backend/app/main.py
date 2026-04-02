import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.agent_ws import router as agent_ws_router
from app.api.router import api_router
from app.config import settings
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.halmed_sync_service import start_sync_scheduler, stop_sync_scheduler

    app.state.http_client = httpx.AsyncClient(timeout=settings.CEZIH_TIMEOUT)
    start_sync_scheduler()
    yield
    stop_sync_scheduler()
    await app.state.http_client.aclose()


app = FastAPI(
    title="HM Digital Medical MVP",
    description="API za upravljanje pacijentima poliklinike",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

from app.api.auth import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(api_router, prefix="/api")
app.include_router(agent_ws_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
