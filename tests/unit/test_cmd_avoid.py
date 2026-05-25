from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from click.testing import CliRunner

from oure.cli.cmd_avoid import (
    _run_baseline_assessment,
    _run_optimization,
    _run_trade_space,
)
from oure.cli.main import cli
from oure.core.models import (
    CovarianceMatrix,
    OptimizationResult,
    RiskResult,
    StateVector,
    TLERecord,
)


@pytest.fixture
def runner():
    return CliRunner()


@patch("oure.cli.cmd_avoid.TCARefinementEngine")
@patch("oure.cli.cmd_avoid.NumericalPropagator")
def test_run_baseline_assessment_no_conjunction(mock_prop_cls, mock_tca_cls):
    mock_tca = MagicMock()
    mock_tca_cls.return_value = mock_tca
    mock_tca.find_tca.return_value = None

    t0 = datetime.now(UTC)
    p_state = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")
    s_state = StateVector(np.array([7000.1, 0, 0]), np.array([0, 7.5, 0]), t0, "456")
    p_cov = CovarianceMatrix(np.eye(6), t0, "123")
    s_cov = CovarianceMatrix(np.eye(6), t0, "456")

    event, prop = _run_baseline_assessment(
        p_state, s_state, p_cov, s_cov, 150.0, "123", "456"
    )
    assert event is None


@patch("oure.cli.cmd_avoid.TCARefinementEngine")
@patch("oure.cli.cmd_avoid.NumericalPropagator")
@patch("oure.cli.cmd_avoid.RiskCalculator")
def test_run_baseline_assessment_happy(mock_calc_cls, mock_prop_cls, mock_tca_cls):
    t0 = datetime.now(UTC)
    mock_tca = MagicMock()
    mock_tca_cls.return_value = mock_tca
    mock_tca.find_tca.return_value = (t0, 1.0)

    mock_prop = MagicMock()
    mock_prop_cls.return_value = mock_prop
    mock_prop.propagate_to.return_value = StateVector(
        np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123"
    )

    mock_calc = MagicMock()
    mock_calc_cls.return_value = mock_calc

    mock_event = MagicMock()
    mock_risk = RiskResult(mock_event, 1e-4, np.eye(2), 20.0, 1.0, 1.0, "YELLOW")
    mock_calc.compute_pc.return_value = mock_risk

    p_state = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")
    s_state = StateVector(np.array([7000.1, 0, 0]), np.array([0, 7.5, 0]), t0, "456")
    p_cov = CovarianceMatrix(np.eye(6), t0, "123")
    s_cov = CovarianceMatrix(np.eye(6), t0, "456")

    event, prop = _run_baseline_assessment(
        p_state, s_state, p_cov, s_cov, 150.0, "123", "456"
    )
    assert event is not None
    assert event.primary_id == "123"


@patch("oure.cli.cmd_avoid.ManeuverOptimizer")
def test_run_optimization_success(mock_opt_cls):
    mock_opt = MagicMock()
    mock_opt_cls.return_value = mock_opt
    mock_opt.optimize.return_value = OptimizationResult(
        np.array([0.0, 0.0, 0.001]), 1e-6, 10, True, "Success"
    )

    t0 = datetime.now(UTC)
    p_state = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")
    p_cov = CovarianceMatrix(np.eye(6), t0, "123")

    _run_optimization(p_state, p_state, p_cov, p_cov, t0, MagicMock(), 12.0)


@patch("oure.cli.cmd_avoid.ManeuverOptimizer")
def test_run_optimization_failure(mock_opt_cls):
    mock_opt = MagicMock()
    mock_opt_cls.return_value = mock_opt
    mock_opt.optimize.return_value = OptimizationResult(
        np.array([0.0, 0.0, 0.0]), 1e-4, 10, False, "Failed"
    )

    t0 = datetime.now(UTC)
    p_state = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")
    p_cov = CovarianceMatrix(np.eye(6), t0, "123")

    _run_optimization(p_state, p_state, p_cov, p_cov, t0, MagicMock(), 12.0)


@patch("oure.cli.cmd_avoid.TCARefinementEngine")
@patch("oure.cli.cmd_avoid.RiskCalculator")
def test_run_trade_space(mock_calc_cls, mock_tca_cls):
    t0 = datetime.now(UTC)
    mock_tca = MagicMock()
    mock_tca_cls.return_value = mock_tca
    mock_tca.find_tca.return_value = (t0, 1.0)

    mock_calc = MagicMock()
    mock_calc_cls.return_value = mock_calc
    mock_event = MagicMock()
    mock_risk = RiskResult(mock_event, 1e-4, np.eye(2), 20.0, 1.0, 1.0, "RED")
    mock_calc.compute_pc.return_value = mock_risk

    mock_prop = MagicMock()
    mock_prop.propagate_to.return_value = StateVector(
        np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123"
    )

    p_state = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")
    p_cov = CovarianceMatrix(np.eye(6), t0, "123")

    _run_trade_space(
        p_state, p_state, p_cov, p_cov, t0, mock_prop, 12.0, t0, "123", "456"
    )


@patch("oure.cli.main.OUREContext")
@patch("oure.cli.cmd_avoid._run_baseline_assessment")
@patch("oure.cli.cmd_avoid._run_optimization")
def test_avoid_cmd_optimize(
    mock_opt, mock_baseline, mock_ctx_class, runner, sample_tle
):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    mock_ctx.tle_fetcher.fetch.return_value = [
        TLERecord("123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
        TLERecord("456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
    ]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_event = MagicMock()
    mock_event.tca = datetime.now(UTC) + timedelta(hours=24)
    mock_baseline.return_value = (mock_event, MagicMock())

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "avoid",
            "--primary",
            "123",
            "--secondary",
            "456",
            "--burn-time-before-tca",
            "12.0",
            "--optimize",
        ],
    )

    assert result.exit_code == 0
    mock_opt.assert_called_once()


@patch("oure.cli.main.OUREContext")
@patch("oure.cli.cmd_avoid._run_baseline_assessment")
@patch("oure.cli.cmd_avoid._run_trade_space")
def test_avoid_cmd_trade_space(mock_trade, mock_baseline, mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    mock_ctx.tle_fetcher.fetch.return_value = [
        TLERecord("123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
        TLERecord("456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
    ]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_event = MagicMock()
    mock_event.tca = datetime.now(UTC) + timedelta(hours=24)
    mock_baseline.return_value = (mock_event, MagicMock())

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "avoid",
            "--primary",
            "123",
            "--secondary",
            "456",
            "--burn-time-before-tca",
            "12.0",
        ],
        input="n\n",  # Answer no to optimization prompt
    )

    assert result.exit_code == 0
    mock_trade.assert_called_once()


@patch("oure.cli.main.OUREContext")
def test_avoid_cmd_fetch_error(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    mock_ctx.tle_fetcher.fetch.side_effect = Exception("Network error")

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "avoid",
            "--primary",
            "123",
            "--secondary",
            "456",
            "--burn-time-before-tca",
            "12.0",
        ],
    )

    assert result.exit_code != 0
    assert "Data ingestion failed: Network error" in result.output


@patch("oure.cli.main.OUREContext")
def test_avoid_cmd_missing_sat(mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx
    mock_ctx.tle_fetcher.fetch.return_value = [
        TLERecord("123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0)
    ]

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "avoid",
            "--primary",
            "123",
            "--secondary",
            "456",
            "--burn-time-before-tca",
            "12.0",
        ],
    )

    assert result.exit_code != 0
    assert "Satellite data missing for 123 or 456" in result.output


@patch("oure.cli.main.OUREContext")
@patch("oure.cli.cmd_avoid.TCARefinementEngine")
def test_avoid_cmd_no_conjunction(mock_tca_cls, mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    mock_ctx.tle_fetcher.fetch.return_value = [
        TLERecord("123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
        TLERecord("456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
    ]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_tca = MagicMock()
    mock_tca_cls.return_value = mock_tca
    mock_tca.find_tca.return_value = None

    result = runner.invoke(
        cli,
        [
            "--st-username",
            "u",
            "--st-password",
            "p",
            "avoid",
            "--primary",
            "123",
            "--secondary",
            "456",
            "--burn-time-before-tca",
            "12.0",
        ],
    )

    assert result.exit_code == 0
    assert "No conjunction detected in baseline trajectory" in result.output


@patch("oure.cli.main.OUREContext")
@patch("oure.cli.cmd_avoid._run_baseline_assessment")
@patch("oure.cli.cmd_avoid._run_trade_space")
def test_avoid_interactive(mock_trade, mock_baseline, mock_ctx_class, runner):
    mock_ctx = MagicMock()
    mock_ctx_class.return_value = mock_ctx

    mock_ctx.tle_fetcher.fetch.return_value = [
        TLERecord("123", "NAME1", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
        TLERecord("456", "NAME2", "1", "2", datetime.now(UTC), 0, 0, 0, 0, 0, 15.0, 0),
    ]
    mock_ctx.flux_fetcher.get_current_f107.return_value = 150.0

    mock_event = MagicMock()
    mock_event.tca = datetime.now(UTC) + timedelta(hours=24)
    mock_baseline.return_value = (mock_event, MagicMock())

    result = runner.invoke(
        cli,
        ["--st-username", "u", "--st-password", "p", "avoid"],
        input="123\n456\n12.0\nn\n",  # Provide primary, secondary, burn time, and say no to optimization
    )

    assert result.exit_code == 0
    mock_trade.assert_called_once()
