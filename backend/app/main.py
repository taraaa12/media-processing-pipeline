from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.images import router as images_router
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, unhandled_exception_handler
from app.core.logging import setup_logging
from app.db.session import async_engine
from app.schemas.image import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    from pathlib import Path

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield
    await async_engine.dispose()


app = FastAPI(
    title="Intelligent Media Processing Pipeline",
    description="Vehicle image upload and async analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(images_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    db_status = "ok"
    redis_status = "ok"

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        client = aioredis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
    except Exception:
        redis_status = "error"

    status = "healthy" if db_status == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(status=status, database=db_status, redis=redis_status)


@app.get("/", tags=["root"])
async def root():
    return JSONResponse({"message": "Media Processing Pipeline API", "docs": "/docs"})
