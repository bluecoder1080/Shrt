from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.limiter import RateLimiter
from app.core.redis import redis_client
from app.services import url as url_service
from app.services import analytics as analytics_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Clean up Redis connection pool on shutdown
    await redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

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
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve the short code to long URL, register click analytics in the background,
    and redirect the visitor. We use HTTP 307 (Temporary Redirect) instead of 301
    to prevent browsers from caching the redirection, which ensures subsequent clicks
    are sent to our server and counted in our analytics.
    """
    # 1. Resolve short_code (hits cache first)
    url_obj = await url_service.resolve_url(db, short_code)
    
    # 2. Extract visitor information
    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")  # Referer header is misspelled in HTTP specification
    
    # 3. Schedule async click logging background task
    background_tasks.add_task(
        analytics_service.record_click,
        url_obj.id,
        ip_address,
        user_agent,
        referrer,
    )
    
    return RedirectResponse(
        url=url_obj.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
