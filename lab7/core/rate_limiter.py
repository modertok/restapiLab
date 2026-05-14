import time
import uuid
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request

from core.dependencies import get_optional_user
from redis_client import get_redis_client

RATE_LIMITS = {
    "anonymous": (2, 60),        # 2 requests per 60 seconds
    "authenticated": (10, 60),   # 10 requests per 60 seconds
}


async def rate_limit(
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> None:
    """Sliding-window rate limiter.

    Authenticated users: identified by user_id  →  10 req/min.
    Anonymous users:     identified by client IP →   2 req/min.
    """
    user_id = current_user["id"] if current_user else None
    identity = user_id or request.client.host
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    key = f"rate_limit:{identity}"
    now = int(time.time())
    window_start = now - period

    # 1. Remove entries that have slid out of the window
    await redis.zremrangebyscore(key, 0, window_start)

    # 2. Count requests in the current window
    request_count = await redis.zcard(key)

    # 3. Reject if limit reached
    if request_count >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(period)},
        )

    # 4. Record this request (unique member so same-second calls are all counted)
    await redis.zadd(key, {f"{now}:{uuid.uuid4()}": now})

    # 5. Auto-expire the key after the window
    await redis.expire(key, period)
