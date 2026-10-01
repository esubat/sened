import asyncio

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import DbSession
from app.core import storage
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


async def check_database(db: AsyncSession) -> str:
    try:
        await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=settings.health_check_timeout_seconds,
        )
        return "ok"
    except SQLAlchemyError, TimeoutError:
        return "failed"


async def check_storage() -> str:
    try:
        await asyncio.wait_for(
            storage.check_bucket(),
            timeout=settings.health_check_timeout_seconds,
        )
        return "ok"
    except BotoCoreError, ClientError, TimeoutError:
        return "failed"


@router.get("/live")
async def live():
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: DbSession):
    checks = {
        "database": await check_database(db),
        "storage": await check_storage(),
    }

    healthy = all(result == "ok" for result in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK
        if healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if healthy else "unhealthy", "checks": checks},
    )
