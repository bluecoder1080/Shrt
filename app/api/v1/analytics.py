from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.analytics import URLAnalyticsSummaryResponse
from app.services import analytics as analytics_service

router = APIRouter()

@router.get("/{short_code}", response_model=URLAnalyticsSummaryResponse)
async def get_analytics(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analytics_data = await analytics_service.get_url_analytics(db, short_code, current_user.id)
    return analytics_data
