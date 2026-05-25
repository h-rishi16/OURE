from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import httpx

from oure.core.models import TLERecord
from oure.data.spacetrack import SpaceTrackFetcher, compute_tle_quality


def test_compute_tle_quality_edge_cases():
    record = TLERecord("1", "TEST", "", "", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0)

    # Negative age (future epoch somehow)
    record_future = TLERecord(
        "1",
        "TEST",
        "",
        "",
        datetime.now(UTC) + timedelta(days=1),
        0,
        0,
        0,
        0,
        0,
        15.0,
        0,
    )
    assert compute_tle_quality(record_future, 400.0) == 1.0

    # Old age causing 0 penalty
    record_old = TLERecord(
        "1",
        "TEST",
        "",
        "",
        datetime.now(UTC) - timedelta(days=10),
        0,
        0,
        0,
        0,
        0,
        15.0,
        0,
    )
    assert compute_tle_quality(record_old, 300.0) == 0.0


def test_spacetrack_fetcher_login_failure():
    fetcher = SpaceTrackFetcher(username="bad", password="bad")
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Auth Error", request=MagicMock(), response=mock_response
        )
        mock_post.return_value = mock_response

        records = fetcher.fetch(sat_ids=["123"])
        assert len(records) == 1
        assert "MOCK" in records[0].name


def test_spacetrack_fetcher_query_failure():
    fetcher = SpaceTrackFetcher(username="mock", password="mock")

    with (
        patch("httpx.AsyncClient.post") as mock_post,
        patch("httpx.AsyncClient.get") as mock_get,
    ):
        mock_response_login = MagicMock()
        mock_response_login.status_code = 200
        mock_post.return_value = mock_response_login

        mock_response_get = MagicMock()
        mock_response_get.status_code = 500
        mock_response_get.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response_get
        )
        mock_get.return_value = mock_response_get

        records = fetcher.fetch(sat_ids=["456"])
        assert len(records) == 1
        assert records[0].sat_id == "456"
        assert "MOCK" in records[0].name


def test_spacetrack_fetcher_fallback_to_mock():
    # If no credentials, fetch() returns mock data immediately
    fetcher = SpaceTrackFetcher(username="", password="")
    records = fetcher.fetch(sat_ids=["25544"])
    assert len(records) == 1
    assert records[0].sat_id == "25544"


def test_parse_tle_record_bad_epoch():
    fetcher = SpaceTrackFetcher(username="", password="")
    bad_data = {"NORAD_CAT_ID": "123", "EPOCH": "invalid-date", "MEAN_MOTION": "0"}
    record = fetcher._parse_tle_record(bad_data)
    assert record.sat_id == "123"
    # Fallback epoch is used (now)
    assert abs((datetime.now(UTC) - record.epoch).total_seconds()) < 5.0


@patch("oure.data.spacetrack.httpx.AsyncClient")
def test_fetch_all_leo_caching(mock_client_cls):
    fetcher = SpaceTrackFetcher(username="mock", password="mock")

    # Mock cache hit for all-leo
    mock_cache = MagicMock()
    mock_cache.get.return_value = "fresh"
    mock_cache.get_all_tles.return_value = [
        TLERecord("999", "MOCK", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.5, 0)
    ]
    fetcher.cache = mock_cache

    # This should return cached results instantly
    records = fetcher.fetch(sat_ids=None)
    assert len(records) == 1
    assert records[0].sat_id == "999"
    mock_cache.get.assert_called_with("spacetrack_bulk_leo")


@patch("oure.data.spacetrack.httpx.AsyncClient")
def test_fetch_chunks(mock_client_cls):
    # Reduce chunk size to 2 to force chunking
    fetcher = SpaceTrackFetcher(username="mock", password="mock")
    fetcher.CHUNK_SIZE = 2

    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "NORAD_CAT_ID": "1",
            "OBJECT_NAME": "N1",
            "TLE_LINE1": "1",
            "TLE_LINE2": "2",
            "EPOCH": "2025-05-09T12:00:00Z",
            "INCLINATION": "0",
            "RA_OF_ASC_NODE": "0",
            "ECCENTRICITY": "0",
            "ARG_OF_PERICENTER": "0",
            "MEAN_ANOMALY": "0",
            "MEAN_MOTION": "15.0",
            "BSTAR": "0",
        },
        {
            "NORAD_CAT_ID": "2",
            "OBJECT_NAME": "N2",
            "TLE_LINE1": "1",
            "TLE_LINE2": "2",
            "EPOCH": "2025-05-09T12:00:00Z",
            "INCLINATION": "0",
            "RA_OF_ASC_NODE": "0",
            "ECCENTRICITY": "0",
            "ARG_OF_PERICENTER": "0",
            "MEAN_ANOMALY": "0",
            "MEAN_MOTION": "15.0",
            "BSTAR": "0",
        },
    ]
    mock_client.get.return_value = mock_response
    mock_response_post = MagicMock()
    mock_response_post.status_code = 200
    mock_client.post.return_value = mock_response_post

    mock_cache = MagicMock()
    fetcher.cache = mock_cache

    # 5 IDs should result in 3 chunks
    records = fetcher.fetch(sat_ids=["1", "2", "3", "4", "5"], force_refresh=True)
    assert len(records) > 0
    # verify cache_tle is called
    mock_cache.cache_tle.assert_called()
