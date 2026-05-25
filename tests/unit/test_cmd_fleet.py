import concurrent.futures
import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from click.testing import CliRunner

from oure.cli.cmd_fleet import _screen_single_primary
from oure.cli.main import cli
from oure.core.models import RiskResult, TLERecord


@pytest.fixture
def runner():
    return CliRunner()


def test_screen_single_primary_happy_path(sample_tle):
    # Mock everything to just test the flow
    with (
        patch("oure.cli.cmd_fleet._tle_to_initial_state") as mock_state,
        patch("oure.cli.cmd_fleet.PropagatorFactory.build") as mock_prop,
        patch("oure.cli.cmd_fleet._default_covariance") as mock_cov,
        patch("oure.cli.cmd_fleet.ConjunctionAssessor") as mock_assessor_cls,
        patch("oure.cli.cmd_fleet.RiskCalculator") as mock_calc_cls,
    ):
        mock_assessor = MagicMock()
        mock_assessor_cls.return_value = mock_assessor
        # Return one mock event
        mock_assessor.find_conjunctions.return_value = ["event"]

        mock_calc = MagicMock()
        mock_calc_cls.return_value = mock_calc
        mock_event = MagicMock()
        mock_event.primary_id = "123"
        mock_event.secondary_id = "456"
        mock_event.tca = datetime.now(UTC)
        mock_event.miss_distance_km = 1.0
        mock_event.relative_velocity_km_s = 7.0
        mock_risk = RiskResult(mock_event, 1e-4, np.eye(2), 20.0, 1.0, 1.0, "YELLOW")
        mock_calc.compute_pc.return_value = mock_risk

        records = {"123": sample_tle, "456": sample_tle}

        results = _screen_single_primary(
            "123", sample_tle, ["456", "789", "123"], records, 150.0, 72.0, 5.0, 20.0
        )

        assert len(results) == 1
        assert results[0] == mock_risk


def test_screen_single_primary_exception(sample_tle):
    with patch(
        "oure.cli.cmd_fleet._tle_to_initial_state", side_effect=Exception("error")
    ):
        records = {"123": sample_tle}
        results = _screen_single_primary(
            "123", sample_tle, ["456"], records, 150.0, 72.0, 5.0, 20.0
        )
        assert results == []


@patch("oure.cli.main.OUREContext")
@patch(
    "oure.cli.cmd_fleet.ProcessPoolExecutor", new=concurrent.futures.ThreadPoolExecutor
)
@patch("oure.cli.cmd_fleet._screen_single_primary")
def test_analyze_fleet_happy_path(
    mock_screen, mock_ctx_class, runner, tmp_path, sample_tle
):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    # We must use real objects, not mocks, because ProcessPoolExecutor pickles them
    tle_123 = TLERecord(
        "123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 0, 0
    )
    tle_456 = TLERecord(
        "456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 0, 0
    )

    # Mock records returned by fetcher
    mock_ctx.tle_fetcher.fetch.return_value = [tle_123, tle_456]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_event = MagicMock()
    mock_event.primary_id = "123"
    mock_event.secondary_id = "456"
    mock_event.tca = datetime.now(UTC)
    mock_event.miss_distance_km = 1.0
    mock_event.relative_velocity_km_s = 7.0
    mock_screen.return_value = [
        RiskResult(mock_event, 1e-4, np.eye(2), 20.0, 1.0, 1.0, "YELLOW")
    ]

    primaries_file = tmp_path / "primaries.json"
    primaries_file.write_text(json.dumps(["123"]))

    secondaries_file = tmp_path / "secondaries.json"
    secondaries_file.write_text(json.dumps(["456"]))

    output_file = tmp_path / "out.json"

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze-fleet",
            "--primaries-file",
            str(primaries_file),
            "--secondaries-file",
            str(secondaries_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Saved 1 total events" in result.output
    assert output_file.exists()


@patch("oure.cli.main.OUREContext")
def test_analyze_fleet_file_error(mock_ctx_class, runner, tmp_path):
    # Pass non-existent files
    primaries_file = tmp_path / "nonexistent.json"
    secondaries_file = tmp_path / "nonexistent2.json"
    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze-fleet",
            "--primaries-file",
            str(primaries_file),
            "--secondaries-file",
            str(secondaries_file),
        ],
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


@patch("oure.cli.main.OUREContext")
def test_analyze_fleet_json_error(mock_ctx_class, runner, tmp_path):
    # Existent files but bad JSON
    primaries_file = tmp_path / "primaries.json"
    primaries_file.write_text("bad json")

    secondaries_file = tmp_path / "secondaries.json"
    secondaries_file.write_text("bad json")

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze-fleet",
            "--primaries-file",
            str(primaries_file),
            "--secondaries-file",
            str(secondaries_file),
        ],
    )
    assert result.exit_code != 0
    assert "Failed to read fleet files" in result.output


@patch("oure.cli.main.OUREContext")
def test_analyze_fleet_fetch_error(mock_ctx_class, runner, tmp_path):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    mock_ctx.tle_fetcher.fetch.side_effect = Exception("network error")

    primaries_file = tmp_path / "primaries.json"
    primaries_file.write_text(json.dumps(["123"]))

    secondaries_file = tmp_path / "secondaries.json"
    secondaries_file.write_text(json.dumps(["456"]))

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze-fleet",
            "--primaries-file",
            str(primaries_file),
            "--secondaries-file",
            str(secondaries_file),
        ],
    )
    assert result.exit_code != 0
    assert "Data fetch failed: network error" in result.output


@patch("oure.cli.main.OUREContext")
@patch(
    "oure.cli.cmd_fleet.ProcessPoolExecutor", new=concurrent.futures.ThreadPoolExecutor
)
@patch("oure.cli.cmd_fleet._screen_single_primary")
def test_analyze_fleet_no_results(mock_screen, mock_ctx_class, runner, tmp_path):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    tle_123 = TLERecord(
        "123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 0, 0
    )
    tle_456 = TLERecord(
        "456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 0, 0
    )

    mock_ctx.tle_fetcher.fetch.return_value = [tle_123, tle_456]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_screen.return_value = []

    primaries_file = tmp_path / "primaries.json"
    primaries_file.write_text(json.dumps(["123"]))

    secondaries_file = tmp_path / "secondaries.json"
    secondaries_file.write_text(json.dumps(["456"]))

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze-fleet",
            "--primaries-file",
            str(primaries_file),
            "--secondaries-file",
            str(secondaries_file),
        ],
    )

    assert result.exit_code == 0
    assert "No conjunctions found across the fleet" in result.output
