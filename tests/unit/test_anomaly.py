from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from oure.core.models import StateVector
from oure.physics.anomaly_detection import ManeuverDetector
from oure.physics.base import BasePropagator


class MockPropagator(BasePropagator):
    def propagate(self, state: StateVector, dt_seconds: float) -> StateVector:
        new_epoch = state.epoch + timedelta(seconds=dt_seconds)
        new_r = state.r + state.v * dt_seconds
        return StateVector(r=new_r, v=state.v, epoch=new_epoch, sat_id=state.sat_id)

    def propagate_to(self, state: StateVector, target_epoch: datetime) -> StateVector:
        dt = (target_epoch - state.epoch).total_seconds()
        return self.propagate(state, dt)

    def propagate_many_to(
        self, states_6d: np.ndarray, current_epoch: datetime, target_epoch: datetime
    ) -> np.ndarray:
        dt = (target_epoch - current_epoch).total_seconds()
        res = states_6d.copy()
        res[:, :3] += res[:, 3:] * dt
        return res


def test_maneuver_detector_nominal():
    prop = MockPropagator()
    detector = ManeuverDetector(propagator=prop, position_threshold_km=10.0)

    t0 = datetime.now(UTC)
    state1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")

    # Exactly matching the prediction
    t1 = t0 + timedelta(seconds=100)
    expected_state = prop.propagate_to(state1, t1)

    report = detector.detect(state1, expected_state)
    assert not report.is_anomaly
    assert report.position_diff_km < 1e-5


def test_maneuver_detector_anomaly():
    prop = MockPropagator()
    detector = ManeuverDetector(propagator=prop, position_threshold_km=10.0)

    t0 = datetime.now(UTC)
    state1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")

    # Diverging state
    t1 = t0 + timedelta(seconds=100)
    expected_state = prop.propagate_to(state1, t1)

    # Introduce a 15km shift
    anomalous_r = expected_state.r + np.array([15.0, 0, 0])
    anomalous_state = StateVector(
        r=anomalous_r, v=expected_state.v, epoch=t1, sat_id="123"
    )

    report = detector.detect(state1, anomalous_state)
    assert report.is_anomaly
    assert report.position_diff_km == pytest.approx(15.0)


def test_maneuver_detector_invalid_epoch():
    prop = MockPropagator()
    detector = ManeuverDetector(propagator=prop, position_threshold_km=10.0)

    t0 = datetime.now(UTC)
    state1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "123")
    state2 = StateVector(
        np.array([7000.0, 0, 0]),
        np.array([0, 7.5, 0]),
        t0 - timedelta(seconds=10),
        "123",
    )

    with pytest.raises(ValueError, match="strictly after"):
        detector.detect(state1, state2)
