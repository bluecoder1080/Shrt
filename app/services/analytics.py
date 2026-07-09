from typing import Dict, Any, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.url import URL
from app.models.click import ClickEvent
from app.core.exceptions import NotFoundError, ForbiddenError

async def record_click(
    url_id: int,
    ip_address: str | None,
    user_agent: str | None,
    referrer: str | None,
) -> None:
    """
    Log a click event. Runs in a background task with its own database session
    to prevent session cleanup conflicts with the main request thread.
    """
    async with AsyncSessionLocal() as db:
        click = ClickEvent(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )
        db.add(click)
        await db.commit()

async def get_url_analytics(db: AsyncSession, short_code: str, user_id: Any) -> Dict[str, Any]:
    # Fetch URL
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = result.scalars().first()
    if not url:
        raise NotFoundError("URL not found")
        
    if url.user_id != user_id:
        raise ForbiddenError("Not authorized to view analytics for this URL")

    # Fetch total clicks count
    count_query = select(func.count(ClickEvent.id)).where(ClickEvent.url_id == url.id)
    count_res = await db.execute(count_query)
    total_clicks = count_res.scalar() or 0

    # Fetch last 100 click events
    clicks_query = (
        select(ClickEvent)
        .where(ClickEvent.url_id == url.id)
        .order_by(ClickEvent.clicked_at.desc())
        .limit(100)
    )
    clicks_res = await db.execute(clicks_query)
    clicks = list(clicks_res.scalars().all())

    return {
        "short_code": url.short_code,
        "original_url": url.original_url,
        "total_clicks": total_clicks,
        "clicks": clicks,
    }
