import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import click
import numpy as np
import pytest
from click.testing import CliRunner

from oure.cli.cmd_analyze import validate_norad_id
from oure.cli.main import cli
from oure.core.models import RiskResult, TLERecord


@pytest.fixture
def runner():
    return CliRunner()


def test_validate_norad_id():
    ctx = MagicMock()
    param = MagicMock()

    # None value
    assert validate_norad_id(ctx, param, None) is None

    # Valid single value
    assert validate_norad_id(ctx, param, "123") == "123"

    # Invalid single value
    with pytest.raises(click.BadParameter):
        validate_norad_id(ctx, param, "123a")

    # Valid tuple
    assert validate_norad_id(ctx, param, ("123", "456")) == ("123", "456")

    # Invalid tuple
    with pytest.raises(click.BadParameter):
        validate_norad_id(ctx, param, ("123", "456a"))


@patch("oure.cli.main.OUREContext")
@patch("oure.cli.cmd_analyze.ConjunctionAssessor")
@patch("oure.cli.cmd_analyze.RiskCalculator")
def test_analyze_happy_path(
    mock_calc_cls, mock_assessor_cls, mock_ctx_class, runner, tmp_path, sample_tle
):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    tle_123 = TLERecord(
        "123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0
    )
    tle_456 = TLERecord(
        "456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0
    )

    mock_ctx.tle_fetcher.fetch.return_value = [tle_123, tle_456]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_assessor = MagicMock()
    mock_assessor_cls.return_value = mock_assessor

    mock_event = MagicMock()
    mock_event.primary_id = "123"
    mock_event.secondary_id = "456"
    mock_event.tca = datetime.now(UTC)
    mock_event.miss_distance_km = 1.0
    mock_event.relative_velocity_km_s = 7.0
    mock_assessor.find_conjunctions.return_value = [mock_event]

    mock_calc = MagicMock()
    mock_calc_cls.return_value = mock_calc
    mock_risk = RiskResult(mock_event, 1e-4, np.eye(2), 20.0, 1.0, 1.0, "YELLOW")
    mock_calc.compute_pc.return_value = mock_risk

    secondaries_file = tmp_path / "sec.json"
    secondaries_file.write_text(json.dumps(["456"]))

    output_file = tmp_path / "out.json"

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze",
            "--primary",
            "123",
            "--secondaries-file",
            str(secondaries_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Found 1 conjunction" in result.output
    assert output_file.exists()


@patch("oure.cli.main.OUREContext")
def test_analyze_no_secondaries(mock_ctx_class, runner):
    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze",
            "--primary",
            "123",
        ],
    )
    assert result.exit_code != 0
    assert "No secondary satellites specified" in result.output


@patch("oure.cli.main.OUREContext")
def test_analyze_bad_json_file(mock_ctx_class, runner, tmp_path):
    sec_file = tmp_path / "sec.json"
    sec_file.write_text("bad json")

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze",
            "--primary",
            "123",
            "--secondaries-file",
            str(sec_file),
        ],
    )
    assert result.exit_code != 0
    assert "Failed to read secondaries file" in result.output


@patch("oure.cli.main.OUREContext")
def test_analyze_fetch_error(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    mock_ctx.tle_fetcher.fetch.side_effect = Exception("network error")

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze",
            "--primary",
            "123",
            "--secondary",
            "456",
        ],
    )
    assert result.exit_code != 0
    assert "Data fetch failed" in result.output


@patch("oure.cli.main.OUREContext")
def test_analyze_primary_missing(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    tle_456 = TLERecord(
        "456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0
    )
    mock_ctx.tle_fetcher.fetch.return_value = [tle_456]

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze",
            "--primary",
            "123",
            "--secondary",
            "456",
        ],
    )
    assert result.exit_code != 0
    assert "Primary 123 not found" in result.output


@patch("oure.cli.main.OUREContext")
@patch("oure.cli.cmd_analyze.ConjunctionAssessor")
def test_analyze_secondary_missing(
    mock_assessor_cls, mock_ctx_class, runner, sample_tle
):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    tle_123 = TLERecord(
        "123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0
    )
    mock_ctx.tle_fetcher.fetch.return_value = [tle_123]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_assessor = MagicMock()
    mock_assessor_cls.return_value = mock_assessor
    mock_assessor.find_conjunctions.return_value = []

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "analyze",
            "--primary",
            "123",
            "--secondary",
            "456",
        ],
    )

    assert result.exit_code == 0
    assert "456 not in cache" in result.output
    assert "No conjunctions found" in result.output
