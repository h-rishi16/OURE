from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from oure.cli.utils import _default_covariance, _tle_to_initial_state
from oure.conjunction.assessor import ConjunctionAssessor
from oure.core.models import ConjunctionEvent
from oure.data.noaa import NOAASolarFluxFetcher
from oure.data.spacetrack import SpaceTrackFetcher
from oure.physics.factory import PropagatorFactory
from oure.risk.calculator import RiskCalculator


@dataclass
class WatchlistAlert:
    asset_norad_id: str
    conjunction: ConjunctionEvent
    triggered_at: datetime
    alert_level: Literal["NOMINAL", "MONITOR", "ACTION"]
    pc: float


class WatchlistMonitor:
    def __init__(
        self,
        assets: list[str],
        pc_threshold: float = 1e-4,
        check_interval_minutes: int = 5,
    ):
        self.assets = assets
        self.pc_threshold = pc_threshold
        self.check_interval_minutes = check_interval_minutes

    def run_screening(self) -> list[ConjunctionEvent]:
        from oure.core.config import settings

        tle_fetcher = SpaceTrackFetcher(
            username=settings.spacetrack_user,
            password=settings.spacetrack_pass,
        )
        flux_fetcher = NOAASolarFluxFetcher()
        flux = flux_fetcher.get_current_f107()

        all_records = tle_fetcher.fetch()
        records_dict = {r.sat_id: r for r in all_records}

        events = []
        assessor = ConjunctionAssessor(screening_distance_km=5.0)

        for primary_id in self.assets:
            if primary_id not in records_dict:
                continue

            primary_tle = records_dict[primary_id]
            primary_state = _tle_to_initial_state(primary_tle)
            primary_prop = PropagatorFactory.build(primary_tle, solar_flux=flux)
            primary_cov = _default_covariance(primary_id)

            secondaries_data = []
            for sid, tle in records_dict.items():
                if sid == primary_id:
                    continue
                prop = PropagatorFactory.build(tle, solar_flux=flux)
                state = _tle_to_initial_state(tle)
                cov = _default_covariance(sid)
                secondaries_data.append((state, cov, prop))

            primary_events = assessor.find_conjunctions(
                primary_state,
                primary_cov,
                primary_prop,
                secondaries_data,
                look_ahead_hours=72.0,
            )
            events.extend(primary_events)

        return events

    def get_alerts(self) -> list[WatchlistAlert]:
        events = self.run_screening()
        calculator = RiskCalculator(hard_body_radius_m=20.0)
        alerts = []
        for event in events:
            res = calculator.compute_pc(event)
            level: Literal["NOMINAL", "MONITOR", "ACTION"]
            if res.pc <= 1e-5:
                level = "NOMINAL"
            elif 1e-5 < res.pc <= 1e-4:
                level = "MONITOR"
            else:
                level = "ACTION"

            alerts.append(
                WatchlistAlert(
                    asset_norad_id=event.primary_id,
                    conjunction=event,
                    triggered_at=datetime.now(UTC),
                    alert_level=level,
                    pc=res.pc,
                )
            )
        return alerts
