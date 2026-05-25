import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from oure.cli.cmd_fetch import _approx_altitude, _save_tles_to_json
from oure.cli.main import cli
from oure.core.models import TLERecord


@pytest.fixture
def runner():
    return CliRunner()


def test_approx_altitude():
    # Mean motion for ~400km altitude is ~15.5 revs/day
    alt = _approx_altitude(15.5)
    assert 300 < alt < 500

    # Check fallback for negative n
    alt_neg = _approx_altitude(-1)
    assert alt_neg == 400


def test_save_tles_to_json(tmp_path):
    out_file = tmp_path / "out.json"
    r = TLERecord("123", "NAME", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 0, 0)
    _save_tles_to_json([r], out_file)

    assert out_file.exists()
    with open(out_file) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["sat_id"] == "123"
    assert data[0]["name"] == "NAME"


@patch("oure.cli.main.OUREContext")
def test_fetch_happy_path(mock_ctx_class, runner, tmp_path):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    mock_flux = MagicMock()
    mock_flux.f10_7 = 150.0
    mock_flux.date = datetime.now(UTC)
    mock_ctx.flux_fetcher.fetch.return_value = [mock_flux]

    records = []
    for i in range(12):
        records.append(
            TLERecord(
                str(i), f"NAME{i}", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.5, 0
            )
        )
    mock_ctx.tle_fetcher.fetch.return_value = records

    out_file = tmp_path / "out.json"

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "fetch",
            "--sat-id",
            "123",
            "--output",
            str(out_file),
        ],
    )

    assert result.exit_code == 0
    assert "F10.7 = 150.0 sfu" in result.output
    assert "Processed 12 TLE records" in result.output
    assert "and 2 more satellites hidden" in result.output
    assert out_file.exists()


@patch("oure.cli.main.OUREContext")
def test_fetch_all_leo(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    mock_ctx.flux_fetcher.fetch.return_value = []
    mock_ctx.tle_fetcher.fetch.return_value = [
        TLERecord("123", "NAME", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.5, 0)
    ]

    result = runner.invoke(
        cli,
        ["--st-username", "u", "--st-password", "p", "fetch", "--all-leo"],
    )

    assert result.exit_code == 0
    assert "Fetching all LEO catalog objects" in result.output


@patch("oure.cli.main.OUREContext")
def test_fetch_no_args(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    mock_ctx.flux_fetcher.fetch.return_value = []

    result = runner.invoke(
        cli,
        ["--st-username", "u", "--st-password", "p", "fetch"],
    )

    assert result.exit_code == 0
    assert "No satellites specified" in result.output


@patch("oure.cli.main.OUREContext")
def test_fetch_error(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    mock_ctx.flux_fetcher.fetch.return_value = []
    mock_ctx.tle_fetcher.fetch.side_effect = Exception("network error")

    result = runner.invoke(
        cli,
        ["--st-username", "u", "--st-password", "p", "fetch", "--sat-id", "123"],
    )

    assert result.exit_code != 0
    assert "Critical Fetch Error: network error" in result.output
