import time
from fastapi import HTTPException, status, Request
from app.core.redis import redis_client

class RateLimiter:
    def __init__(self, window_seconds: int, max_requests: int, endpoint_name: str):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.endpoint_name = endpoint_name

    async def __call__(self, request: Request):
        # Retrieve client IP, taking proxy headers into account
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        key = f"rate_limit:{self.endpoint_name}:{client_ip}"
        now = time.time()
        clear_before = now - self.window_seconds
        
        try:
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, "-inf", clear_before)
                # Use a unique member value (timestamp + random counter or float) to avoid overwriting elements
                pipe.zadd(key, {f"{now}:{client_ip}": now})
                pipe.zcard(key)
                pipe.expire(key, self.window_seconds)
                results = await pipe.execute()
                
            count = results[2]
            if count > self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )
        except HTTPException:
            raise
        except Exception:
            # Fallback gracefully or log. For production, if Redis is down, we allow the request to pass.
            pass
