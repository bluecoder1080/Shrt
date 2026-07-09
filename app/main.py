from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.deps import get_db
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.limiter import RateLimiter
from app.core.redis import redis_client
from app.services import url as url_service
from app.tasks.analytics import log_click_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Clean up Redis connection pool on shutdown
    await redis_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

# Trust X-Forwarded-Proto / X-Forwarded-For from Vercel / any reverse proxy
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register global application exception handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Register API routes
app.include_router(api_router, prefix="/api/v1")

# Instantiate rate limiter for redirect endpoint
redirect_limiter = RateLimiter(
    window_seconds=settings.RATE_LIMIT_REDIRECT_WINDOW,
    max_requests=settings.RATE_LIMIT_REDIRECT_MAX_REQUESTS,
    endpoint_name="redirect",
)


@app.get(
    "/{short_code}",
    dependencies=[Depends(redirect_limiter)],
    response_class=RedirectResponse,
)
async def redirect_to_long_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve the short code to long URL, enqueue click logging task to RabbitMQ,
    and redirect the visitor immediately.
    """
    # 1. Resolve short_code (hits cache first)
    url_obj = await url_service.resolve_url(db, short_code)

    # 2. Extract visitor information
    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip_address = (
        x_forwarded_for.split(",")[0].strip()
        if x_forwarded_for
        else (request.client.host if request.client else None)
    )
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get(
        "referer"
    )  # Referer header is misspelled in HTTP specification

    # 3. Push click event to RabbitMQ queue via Celery
    log_click_task.delay(
        url_obj.id,
        ip_address,
        user_agent,
        referrer,
        datetime.now(timezone.utc).isoformat(),
    )

    return RedirectResponse(
        url=url_obj.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
