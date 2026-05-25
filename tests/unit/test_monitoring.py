from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from oure.core.models import ConjunctionEvent, CovarianceMatrix, StateVector, TLERecord
from oure.monitoring.alerting import AlertDispatcher
from oure.monitoring.watchlist import WatchlistAlert, WatchlistMonitor


def test_alert_dispatcher_with_webhook():
    epoch = datetime.now(UTC)
    state = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), epoch, "123")
    cov = CovarianceMatrix(np.eye(6), epoch, "123")
    event = ConjunctionEvent(
        primary_id="123",
        secondary_id="456",
        tca=epoch,
        miss_distance_km=0.5,
        relative_velocity_km_s=15.0,
        primary_state=state,
        secondary_state=state,
        primary_covariance=cov,
        secondary_covariance=cov,
    )
    alert = WatchlistAlert(
        asset_norad_id="123",
        conjunction=event,
        triggered_at=epoch,
        alert_level="ACTION",
        pc=0.001,
    )

    dispatcher = AlertDispatcher(webhook_url="http://dummy.url")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        dispatcher.dispatch(alert)
        mock_urlopen.assert_called_once()

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 500
        mock_urlopen.return_value.__enter__.return_value = mock_response
        dispatcher.dispatch(alert)
        mock_urlopen.assert_called_once()

    with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        dispatcher.dispatch(alert)


@pytest.mark.req("REQ-OPS-01")
def test_watchlist_monitor_run_screening_and_alerts():
    monitor = WatchlistMonitor(assets=["123"], pc_threshold=1e-4)

    epoch = datetime.now(UTC)
    mock_record1 = TLERecord(
        "123", "SAT1", "line1", "line2", epoch, 0, 0, 0, 0, 0, 15.0, 0
    )
    mock_record2 = TLERecord(
        "456", "SAT2", "line1", "line2", epoch, 0, 0, 0, 0, 0, 15.0, 0
    )

    with patch("oure.monitoring.watchlist.SpaceTrackFetcher") as mock_fetcher_cls:
        mock_fetcher = mock_fetcher_cls.return_value
        mock_fetcher.fetch.return_value = [mock_record1, mock_record2]

        with patch("oure.monitoring.watchlist.NOAASolarFluxFetcher") as mock_flux_cls:
            mock_flux = mock_flux_cls.return_value
            mock_flux.get_current_f107.return_value = 150.0

            with patch(
                "oure.monitoring.watchlist.ConjunctionAssessor"
            ) as mock_assessor_cls:
                mock_assessor = mock_assessor_cls.return_value
                state = StateVector(
                    np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), epoch, "123"
                )
                cov = CovarianceMatrix(np.eye(6), epoch, "123")
                event = ConjunctionEvent(
                    "123", "456", epoch, 0.5, 15.0, state, state, cov, cov
                )
                mock_assessor.find_conjunctions.return_value = [event]

                with patch("oure.monitoring.watchlist.RiskCalculator") as mock_calc_cls:
                    mock_calc = mock_calc_cls.return_value
                    res_mock = MagicMock()
                    res_mock.pc = 1e-3
                    mock_calc.compute_pc.return_value = res_mock

                    alerts = monitor.get_alerts()
                    assert len(alerts) == 1
                    assert alerts[0].alert_level == "ACTION"

                    res_mock.pc = 5e-5
                    alerts = monitor.get_alerts()
                    assert alerts[0].alert_level == "MONITOR"

                    res_mock.pc = 1e-6
                    alerts = monitor.get_alerts()
                    assert alerts[0].alert_level == "NOMINAL"
