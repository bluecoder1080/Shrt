import asyncio
from collections import defaultdict
from datetime import datetime, date, timezone
from typing import Optional
import geoip2.database
from user_agents import parse as parse_ua
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.click import ClickEvent
from app.models.summary import (
    DailyClicksSummary,
    CountryClicksSummary,
    ReferrerClicksSummary,
    DeviceClicksSummary,
)

async def async_log_click(
    url_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    referrer: Optional[str],
    clicked_at_iso: str,
) -> None:
    # 1. Parse User Agent
    device = "Unknown"
    browser = "Unknown"
    os = "Unknown"
    if user_agent:
        try:
            parsed = parse_ua(user_agent)
            device = parsed.device.family or "Unknown"
            browser = parsed.browser.family or "Unknown"
            os = parsed.os.family or "Unknown"
        except Exception:
            pass

    # 2. Lookup Geolocation
    country_code = "Unknown"
    if ip_address:
        try:
            with geoip2.database.Reader(settings.GEOIP_DATABASE_PATH) as reader:
                response = reader.country(ip_address)
                country_code = response.country.iso_code or "Unknown"
        except Exception:
            # Gracefully default to Unknown if GeoIP DB is missing or IP is local/invalid
            country_code = "Unknown"

    # 3. Save to database
    async with AsyncSessionLocal() as db:
        click = ClickEvent(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer or "Direct",
            country_code=country_code,
            device_family=device,
            browser_family=browser,
            os_family=os,
            aggregated=False,
            clicked_at=datetime.fromisoformat(clicked_at_iso),
        )
        db.add(click)
        await db.commit()

@celery_app.task(bind=True, max_retries=5)
def log_click_task(
    self,
    url_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    referrer: Optional[str],
    clicked_at_iso: str,
) -> None:
    """Async task to enrich and log a URL click event."""
    try:
        asyncio.run(async_log_click(url_id, ip_address, user_agent, referrer, clicked_at_iso))
    except Exception as exc:
        # Exponential backoff retry countdown: 5s, 7s, 9s, 13s, 21s...
        raise self.retry(exc=exc, countdown=(2 ** self.request.retries) + 5)


async def async_aggregate_clicks() -> None:
    async with AsyncSessionLocal() as db:
        # Fetch a batch of unaggregated clicks
        result = await db.execute(
            select(ClickEvent)
            .where(ClickEvent.aggregated == False)
            .limit(5000)
        )
        batch = list(result.scalars().all())
        if not batch:
            return

        # Initialize counters
        daily_counts = defaultdict(int)
        country_counts = defaultdict(int)
        referrer_counts = defaultdict(int)
        device_counts = defaultdict(int)

        # Process clicks in memory
        for click in batch:
            url_id = click.url_id
            click_date = click.clicked_at.date()
            country = click.country_code or "Unknown"
            referrer = click.referrer or "Direct"
            device = click.device_family or "Unknown"
            browser = click.browser_family or "Unknown"
            os_name = click.os_family or "Unknown"

            daily_counts[(url_id, click_date)] += 1
            country_counts[(url_id, country)] += 1
            referrer_counts[(url_id, referrer)] += 1
            device_counts[(url_id, device, browser, os_name)] += 1

        # Perform Upserts into Daily clicks summary
        for (url_id, click_date), count in daily_counts.items():
            stmt = insert(DailyClicksSummary).values(
                url_id=url_id, date=click_date, click_count=count
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["url_id", "date"],
                set_={"click_count": DailyClicksSummary.click_count + stmt.excluded.click_count},
            )
            await db.execute(stmt)

        # Perform Upserts into Country clicks summary
        for (url_id, country), count in country_counts.items():
            stmt = insert(CountryClicksSummary).values(
                url_id=url_id, country_code=country, click_count=count
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["url_id", "country_code"],
                set_={"click_count": CountryClicksSummary.click_count + stmt.excluded.click_count},
            )
            await db.execute(stmt)

        # Perform Upserts into Referrer clicks summary
        for (url_id, referrer), count in referrer_counts.items():
            stmt = insert(ReferrerClicksSummary).values(
                url_id=url_id, referrer=referrer, click_count=count
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["url_id", "referrer"],
                set_={"click_count": ReferrerClicksSummary.click_count + stmt.excluded.click_count},
            )
            await db.execute(stmt)

        # Perform Upserts into Device clicks summary
        for (url_id, device, browser, os_name), count in device_counts.items():
            stmt = insert(DeviceClicksSummary).values(
                url_id=url_id,
                device_family=device,
                browser_family=browser,
                os_family=os_name,
                click_count=count,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["url_id", "device_family", "browser_family", "os_family"],
                set_={"click_count": DeviceClicksSummary.click_count + stmt.excluded.click_count},
            )
            await db.execute(stmt)

        # Mark processed batch click events as aggregated
        click_ids = [click.id for click in batch]
        await db.execute(
            update(ClickEvent)
            .where(ClickEvent.id.in_(click_ids))
            .values(aggregated=True)
        )
        
        await db.commit()

@celery_app.task(bind=True, max_retries=5)
def aggregate_clicks_task(self) -> None:
    """Cron-like task to batch aggregate unaggregated click events into summary tables."""
    try:
        asyncio.run(async_aggregate_clicks())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=(2 ** self.request.retries) + 5)
