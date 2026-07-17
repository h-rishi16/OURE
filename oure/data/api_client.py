import logging
import os
import time

import httpx

logger = logging.getLogger("api_client")


async def fetch_active_tles(
    cache_file: str = "active_tles.txt", max_age_hours: int = 12
) -> str | None:
    if os.path.exists(cache_file):
        file_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
        if file_age_hours < max_age_hours:
            logger.info(f"Using cached TLEs. File age: {file_age_hours:.2f} hours.")
            return cache_file

    logger.info("Fetching fresh TLEs from CelesTrak...")
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(cache_file, "w") as f:
                f.write(response.text)

            logger.info("Successfully fetched and cached fresh TLEs.")
            return cache_file

    except httpx.RequestError as e:
        logger.error(f"Network error while fetching TLEs: {e}")
        if os.path.exists(cache_file):
            logger.warning("Falling back to stale local cache due to network failure.")
            return cache_file
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching TLEs: {e}")
        if os.path.exists(cache_file):
            return cache_file
        return None
