from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.core.config import settings
from app.core.limiter import RateLimiter
from app.models.user import User
from app.schemas.url import URLCreate, URLResponse
from app.services import url as url_service

router = APIRouter()

# Instantiate shorten rate limiter from settings
shorten_limiter = RateLimiter(
    window_seconds=settings.RATE_LIMIT_SHORTEN_WINDOW,
    max_requests=settings.RATE_LIMIT_SHORTEN_MAX_REQUESTS,
    endpoint_name="shorten",
)

@router.post(
    "/",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(shorten_limiter)],
)
async def shorten_url(
    url_in: URLCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    db_url = await url_service.create_short_url(db, url_in, user_id)
    
    base_url = str(request.base_url)
    short_url = f"{base_url}{db_url.short_code}"
    
    return URLResponse(
        id=db_url.id,
        original_url=db_url.original_url,
        short_code=db_url.short_code,
        expires_at=db_url.expires_at,
        created_at=db_url.created_at,
        user_id=db_url.user_id,
        short_url=short_url,
    )

@router.get("/", response_model=List[URLResponse])
async def list_urls(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    urls = await url_service.get_user_urls(db, current_user.id)
    base_url = str(request.base_url)
    
    return [
        URLResponse(
            id=u.id,
            original_url=u.original_url,
            short_code=u.short_code,
            expires_at=u.expires_at,
            created_at=u.created_at,
            user_id=u.user_id,
            short_url=f"{base_url}{u.short_code}",
        )
        for u in urls
    ]

@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await url_service.delete_url(db, short_code, current_user.id)
