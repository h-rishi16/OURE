import os

import click
from redis import ConnectionPool

from oure.api.auth import APIKeyManager

from .main import cli
from .utils import UI


@cli.command()
@click.option("--label", required=True, help="Label for the API key.")
@click.option("--rate-limit", type=int, default=60, help="Rate limit per minute.")
def create_api_key(label: str, rate_limit: int) -> None:
    """Generate a new API key for the FastAPI server."""
    redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    try:
        redis_pool = ConnectionPool.from_url(redis_url)
        manager = APIKeyManager(redis_pool)
        key = manager.create_key(label=label, rate_limit_per_min=rate_limit)
        UI.success(f"Generated API Key for '{label}': [highlight]{key}[/highlight]")
        UI.header("Store this key securely. It will not be shown again.")
    except Exception as e:
        UI.error(f"Failed to generate API key: {e}")
