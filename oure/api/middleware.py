import os

from fastapi import Depends, Header, HTTPException
from redis import ConnectionPool

from oure.api.auth import APIKeyManager

redis_pool = ConnectionPool.from_url(
    os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
)


def get_key_manager() -> APIKeyManager:
    return APIKeyManager(redis_pool)


async def require_api_key(
    x_api_key: str = Header(...), manager: APIKeyManager = Depends(get_key_manager)
) -> str:
    if not manager.validate_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if not manager.check_rate_limit(x_api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    label = manager.redis.hget(f"apikey:{x_api_key}", "label")
    if label:
        return label.decode("utf-8") if isinstance(label, bytes) else str(label)
    return "unknown"
