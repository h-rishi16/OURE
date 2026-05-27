from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import numpy as np

from oure.conjunction.assessor import ConjunctionAssessor
from oure.core.models import CovarianceMatrix, StateVector


class MockProp:
    def __init__(self, id_str):
        self.prop_id = id_str
        self.calls = 0

    def propagate_to(self, state, epoch):
        self.calls += 1
        return StateVector(r=state.r, v=state.v, epoch=epoch, sat_id=state.sat_id)

    def propagate_sequence(self, state, epochs):
        self.calls += 1
        return [
            StateVector(r=state.r, v=state.v, epoch=epoch, sat_id=state.sat_id)
            for epoch in epochs
        ]


def test_assessor_proximity_filter_failures():
    assessor = ConjunctionAssessor(
        screening_distance_km=50000.0, tca_time_step_s=3600.0
    )

    t0 = datetime.now(UTC)
    primary = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "P")
    p_prop = MockProp("P")

    sec_state = StateVector(np.array([7000.1, 0, 0]), np.array([0, 7.5, 0]), t0, "S1")
    s_prop = MockProp("S1")

    # Mock to throw exception on propagate_sequence
    s_prop.propagate_sequence = MagicMock(side_effect=Exception("Batch failed"))

    secondaries = [(sec_state, None, s_prop)]

    # Should catch exception and place object at 1e9, 1e9, 1e9
    pairs = assessor._proximity_filter(primary, p_prop, secondaries, [0.0], t0)
    assert len(pairs) == 0  # Placed far away, so it doesn't match


def test_assessor_kdtree_path():
    assessor = ConjunctionAssessor(
        screening_distance_km=50000.0, tca_time_step_s=3600.0
    )

    t0 = datetime.now(UTC)
    primary = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "P")
    p_prop = MockProp("P")

    secondaries = []
    # Create > 500 secondaries to trigger KDTree logic
    s_prop = MockProp("S")
    for i in range(505):
        s_state = StateVector(
            np.array([7000.0 + i * 0.001, 0, 0]), np.array([0, 7.5, 0]), t0, f"S{i}"
        )
        secondaries.append((s_state, None, s_prop))

    pairs = assessor._proximity_filter(
        primary, p_prop, secondaries, [0.0, 3600.0, 7200.0], t0
    )
    assert len(pairs) == 505
    # The pairs should track t_min and t_max correctly
    t_min, t_max = pairs[0]
    assert t_min == t0
    assert t_max == t0 + timedelta(seconds=7200)


def test_assessor_golden_section_refinement():
    assessor = ConjunctionAssessor(
        screening_distance_km=50000.0, tca_time_step_s=3600.0
    )

    t0 = datetime.now(UTC)
    primary = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), t0, "P")
    p_cov = CovarianceMatrix(np.eye(6), t0, "P")
    p_prop = MockProp("P")

    sec_state = StateVector(np.array([7000.1, 0, 0]), np.array([0, 7.5, 0]), t0, "S1")
    s_cov = CovarianceMatrix(np.eye(6), t0, "S1")
    s_prop = MockProp("S1")

    secondaries = [(sec_state, s_cov, s_prop)]

    candidate_pairs = {0: (t0, t0 + timedelta(seconds=3600))}

    # Mock TCA finder
    assessor.tca_finder = MagicMock()
    # Return a TCA and miss distance within screening threshold
    assessor.tca_finder.find_tca.return_value = (t0 + timedelta(seconds=1800), 10.0)

    events = assessor._golden_section_refinement(
        primary, p_cov, p_prop, secondaries, candidate_pairs
    )
    assert len(events) == 1
    assert events[0].miss_distance_km == 10.0
    assert events[0].tca == t0 + timedelta(seconds=1800)

    # Return a TCA outside threshold
    assessor.tca_finder.find_tca.return_value = (t0 + timedelta(seconds=1800), 60000.0)
    events2 = assessor._golden_section_refinement(
        primary, p_cov, p_prop, secondaries, candidate_pairs
    )
    assert len(events2) == 0

    # Return None
    assessor.tca_finder.find_tca.return_value = None
    events3 = assessor._golden_section_refinement(
        primary, p_cov, p_prop, secondaries, candidate_pairs
    )
    assert len(events3) == 0
