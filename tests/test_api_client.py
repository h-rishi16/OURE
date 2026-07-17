import os
import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from oure.data.api_client import fetch_active_tles


@pytest.mark.asyncio
async def test_fetch_active_tles_cache_hit() -> None:
    cache_file = "test_active_tles.txt"
    with open(cache_file, "w") as f:
        f.write("mock tle data")
    os.utime(cache_file, (time.time(), time.time()))
    result = await fetch_active_tles(cache_file=cache_file, max_age_hours=12)
    assert result == cache_file
    os.remove(cache_file)


@pytest.mark.asyncio
async def test_fetch_active_tles_cache_miss() -> None:
    cache_file = "test_active_tles_miss.txt"
    if os.path.exists(cache_file):
        os.remove(cache_file)

    class MockResponse:
        def raise_for_status(self) -> None:
            pass

        @property
        def text(self) -> str:
            return "new mock tle data"

    with patch("httpx.AsyncClient.get", return_value=MockResponse()):
        result = await fetch_active_tles(cache_file=cache_file, max_age_hours=12)
        assert result == cache_file
        assert os.path.exists(cache_file)
        with open(cache_file, "r") as f:
            assert f.read() == "new mock tle data"
    if os.path.exists(cache_file):
        os.remove(cache_file)


@pytest.mark.asyncio
async def test_fetch_active_tles_network_error() -> None:
    cache_file = "test_active_tles_error.txt"
    with open(cache_file, "w") as f:
        f.write("stale tle data")
    old_time = time.time() - (13 * 3600)
    os.utime(cache_file, (old_time, old_time))
    with patch(
        "httpx.AsyncClient.get",
        side_effect=httpx.RequestError("Network timeout", request=MagicMock()),
    ):
        result = await fetch_active_tles(cache_file=cache_file, max_age_hours=12)
        assert result == cache_file
    os.remove(cache_file)
