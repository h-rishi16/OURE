import time
import uuid

from redis import ConnectionPool, Redis


class APIKeyManager:
    def __init__(self, redis_pool: ConnectionPool) -> None:
        self.redis = Redis(connection_pool=redis_pool)

    def create_key(self, label: str, rate_limit_per_min: int = 60) -> str:
        key = str(uuid.uuid4())
        # Store key info in Redis: label and rate limit
        self.redis.hset(
            f"apikey:{key}", mapping={"label": label, "rate_limit": rate_limit_per_min}
        )
        return key

    def validate_key(self, key: str) -> bool:
        return bool(self.redis.exists(f"apikey:{key}"))

    def check_rate_limit(self, key: str) -> bool:
        # fixed-window: increment counter in Redis, expire after 60s
        current_minute = int(time.time() // 60)
        rate_key = f"rate:{key}:{current_minute}"

        count = int(self.redis.incr(rate_key))
        if count == 1:
            self.redis.expire(rate_key, 60)

        limit_val = self.redis.hget(f"apikey:{key}", "rate_limit")
        rate_limit = int(limit_val) if limit_val else 60

        if count > rate_limit:
            return False
        return True
