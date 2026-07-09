from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.core.redis import redis_client
from app.core.config import settings
import kombu

router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint probing database, redis, and rabbitmq connectivity."""
    status_report = {
        "status": "healthy",
        "database": "unhealthy",
        "redis": "unhealthy",
        "rabbitmq": "unhealthy",
    }
    
    # 1. Database Check
    try:
        await db.execute(text("SELECT 1"))
        status_report["database"] = "healthy"
    except Exception as e:
        status_report["status"] = "unhealthy"
        status_report["database_error"] = str(e)
        
    # 2. Redis Check
    try:
        await redis_client.ping()
        status_report["redis"] = "healthy"
    except Exception as e:
        status_report["status"] = "unhealthy"
        status_report["redis_error"] = str(e)

    # 3. RabbitMQ Check
    try:
        connection = kombu.Connection(settings.CELERY_BROKER_URL)
        connection.connect()
        connection.release()
        status_report["rabbitmq"] = "healthy"
    except Exception as e:
        status_report["status"] = "unhealthy"
        status_report["rabbitmq_error"] = str(e)

    if status_report["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=status_report,
        )
        
    return status_report
