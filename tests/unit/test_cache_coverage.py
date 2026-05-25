import sqlite3
from datetime import UTC, datetime, timedelta

from oure.core.models import TLERecord
from oure.data.cache import CacheManager


def test_cache_get_risk_history(tmp_path):
    db_path = tmp_path / "test.db"
    cache = CacheManager(db_path)

    tca = datetime.now(UTC)
    cache.log_risk_event("1", "2", tca, 1e-4, 5.0, "YELLOW")
    cache.log_risk_event("1", "2", tca + timedelta(hours=1), 1e-5, 10.0, "GREEN")

    history = cache.get_risk_history("1", "2")
    assert len(history) == 2
    assert history[0]["primary_id"] == "1"
    assert history[0]["pc"] == 1e-4


def test_cache_get_expired(tmp_path):
    db_path = tmp_path / "test.db"
    cache = CacheManager(db_path)

    # Insert manually with old fetched_at
    old_time = datetime.now(UTC).timestamp() - 4000
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO cache_entries (key, value, fetched_at, ttl_seconds) VALUES (?, ?, ?, ?)",
            ("key1", "val1", old_time, 3600.0),
        )

    val = cache.get("key1")
    assert val is None


def test_cache_get_all_tles(tmp_path):
    db_path = tmp_path / "test.db"
    cache = CacheManager(db_path)

    epoch = datetime.now(UTC)
    tle1 = TLERecord("1", "N1", "L1", "L2", epoch, epoch, 0, 0, 0, 0, 0, 0, 0)
    tle2 = TLERecord("2", "N2", "L1", "L2", epoch, epoch, 0, 0, 0, 0, 0, 0, 0)

    cache.cache_tle(tle1)
    cache.cache_tle(tle2)

    tles = cache.get_all_tles()
    assert len(tles) == 2
    assert tles[0].sat_id == "1"
    assert tles[1].sat_id == "2"
