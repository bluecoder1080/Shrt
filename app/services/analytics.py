from collections import defaultdict
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.url import URL
from app.models.summary import (
    DailyClicksSummary,
    CountryClicksSummary,
    ReferrerClicksSummary,
    DeviceClicksSummary,
)
from app.core.exceptions import NotFoundError, ForbiddenError

async def get_url_analytics(db: AsyncSession, short_code: str, user_id: Any) -> Dict[str, Any]:
    # Fetch URL
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = result.scalars().first()
    if not url:
        raise NotFoundError("URL not found")
        
    if url.user_id != user_id:
        raise ForbiddenError("Not authorized to view analytics for this URL")

    # 1. Fetch Daily Clicks Summary (clicks over time)
    daily_res = await db.execute(
        select(DailyClicksSummary)
        .where(DailyClicksSummary.url_id == url.id)
        .order_by(DailyClicksSummary.date.asc())
    )
    daily_clicks = list(daily_res.scalars().all())
    total_clicks = sum(d.click_count for d in daily_clicks)

    # 2. Fetch Country Clicks Summary
    country_res = await db.execute(
        select(CountryClicksSummary)
        .where(CountryClicksSummary.url_id == url.id)
        .order_by(CountryClicksSummary.click_count.desc())
    )
    country_clicks = list(country_res.scalars().all())

    # 3. Fetch Referrer Clicks Summary
    referrer_res = await db.execute(
        select(ReferrerClicksSummary)
        .where(ReferrerClicksSummary.url_id == url.id)
        .order_by(ReferrerClicksSummary.click_count.desc())
    )
    referrer_clicks = list(referrer_res.scalars().all())

    # 4. Fetch Device Clicks Summary (contains dimensions device, browser, os)
    device_res = await db.execute(
        select(DeviceClicksSummary)
        .where(DeviceClicksSummary.url_id == url.id)
    )
    device_clicks = list(device_res.scalars().all())

    # Aggregate browser/device/os counts in memory from pre-summarized subsets
    device_counts = defaultdict(int)
    browser_counts = defaultdict(int)
    os_counts = defaultdict(int)

    for item in device_clicks:
        device_counts[item.device_family] += item.click_count
        browser_counts[item.browser_family] += item.click_count
        os_counts[item.os_family] += item.click_count

    # Convert to response formats
    device_breakdown = [
        {"name": k, "click_count": v}
        for k, v in sorted(device_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    browser_breakdown = [
        {"name": k, "click_count": v}
        for k, v in sorted(browser_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    os_breakdown = [
        {"name": k, "click_count": v}
        for k, v in sorted(os_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "short_code": url.short_code,
        "original_url": url.original_url,
        "total_clicks": total_clicks,
        "clicks_over_time": daily_clicks,
        "top_countries": country_clicks,
        "top_referrers": referrer_clicks,
        "device_breakdown": device_breakdown,
        "browser_breakdown": browser_breakdown,
        "os_breakdown": os_breakdown,
    }
