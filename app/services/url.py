import asyncio
import ipaddress
import json
import socket
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.url import URL
from app.schemas.url import URLCreate
from app.core.redis import redis_client
from app.core.exceptions import ConflictError, NotFoundError, ExpiredError, ValidationError, ForbiddenError

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
CACHE_TTL = 86400  # 24 hours

def encode_base62(num: int) -> str:
    if num == 0:
        return BASE62_ALPHABET[0]
    arr = []
    base = len(BASE62_ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62_ALPHABET[rem])
    arr.reverse()
    return "".join(arr)

async def validate_ssrf(url_str: str) -> None:
    try:
        parsed = urlparse(url_str)
        hostname = parsed.hostname
        if not hostname:
            raise ValidationError("Invalid URL: missing hostname")
        
        # Perform async DNS resolution to avoid blocking the event loop
        addr_info = await asyncio.to_thread(socket.getaddrinfo, hostname, None)
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"SSRF Check: Hostname resolution failed for '{hostname}': {str(e)}")

    for item in addr_info:
        ip_str = item[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise ValidationError("SSRF Protection: Access to private or local network is forbidden")
        except ValueError:
            raise ValidationError("SSRF Protection: Invalid IP address resolved")

async def get_url_by_code(db: AsyncSession, short_code: str) -> Optional[URL]:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    return result.scalars().first()

async def resolve_url(db: AsyncSession, short_code: str) -> URL:
    # 1. Check Redis Cache
    cache_key = f"url:{short_code}"
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)
            
            # Check expiration
            expires_at_str = data.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at <= datetime.now(timezone.utc):
                    # Invalidate expired cache
                    await redis_client.delete(cache_key)
                    raise ExpiredError()
            
            # Create a detached/mock URL object from cache data
            # Note: We need id and original_url for click recording
            url_obj = URL(
                id=data["id"],
                original_url=data["original_url"],
                short_code=short_code,
                expires_at=datetime.fromisoformat(expires_at_str) if expires_at_str else None,
                user_id=data.get("user_id"),
            )
            return url_obj
    except ExpiredError:
        raise
    except Exception:
        # Fallback to database on cache/redis failure
        pass

    # 2. Database Lookup
    url = await get_url_by_code(db, short_code)
    if not url:
        raise NotFoundError("Short URL not found")

    # Check expiration
    if url.expires_at and url.expires_at <= datetime.now(timezone.utc):
        raise ExpiredError()

    # 3. Populate Redis Cache
    try:
        cache_val = {
            "id": url.id,
            "original_url": url.original_url,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
            "user_id": str(url.user_id) if url.user_id else None,
        }
        await redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_val))
    except Exception:
        pass

    return url

async def create_short_url(db: AsyncSession, url_in: URLCreate, user_id: Optional[Any] = None) -> URL:
    # Validate target URL to prevent SSRF
    await validate_ssrf(str(url_in.original_url))

    if url_in.custom_alias:
        # Check for custom alias conflicts
        existing = await get_url_by_code(db, url_in.custom_alias)
        if existing:
            raise ConflictError("Custom alias is already in use")
        short_code = url_in.custom_alias
        url_obj = URL(
            original_url=str(url_in.original_url),
            short_code=short_code,
            expires_at=url_in.expires_at,
            user_id=user_id,
        )
        db.add(url_obj)
        await db.commit()
        await db.refresh(url_obj)
    else:
        # Collision-free short code generation using sequence
        # We loop to guarantee unique generated codes if they conflict with custom aliases
        while True:
            res = await db.execute(text("SELECT nextval('urls_id_seq')"))
            next_id = res.scalar()
            short_code = encode_base62(next_id)
            
            existing = await get_url_by_code(db, short_code)
            if not existing:
                break
        
        url_obj = URL(
            id=next_id,
            original_url=str(url_in.original_url),
            short_code=short_code,
            expires_at=url_in.expires_at,
            user_id=user_id,
        )
        db.add(url_obj)
        await db.commit()
        await db.refresh(url_obj)

    # Populate cache immediately (Cache Warming)
    try:
        cache_val = {
            "id": url_obj.id,
            "original_url": url_obj.original_url,
            "expires_at": url_obj.expires_at.isoformat() if url_obj.expires_at else None,
            "user_id": str(url_obj.user_id) if url_obj.user_id else None,
        }
        await redis_client.setex(f"url:{short_code}", CACHE_TTL, json.dumps(cache_val))
    except Exception:
        pass

    return url_obj

async def delete_url(db: AsyncSession, short_code: str, user_id: Any) -> None:
    url = await get_url_by_code(db, short_code)
    if not url:
        raise NotFoundError("URL not found")
    
    if url.user_id != user_id:
        raise ForbiddenError("Not authorized to delete this URL")

    await db.delete(url)
    await db.commit()

    # Invalidate Cache
    try:
        await redis_client.delete(f"url:{short_code}")
    except Exception:
        pass

async def get_user_urls(db: AsyncSession, user_id: Any) -> List[URL]:
    result = await db.execute(select(URL).where(URL.user_id == user_id).order_by(URL.created_at.desc()))
    return list(result.scalars().all())
