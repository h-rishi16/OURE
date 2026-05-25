from datetime import UTC, datetime, timedelta

import numpy as np

from oure.core.models import TLERecord
from oure.data.spacetrack import compute_tle_quality
from oure.physics.numerical import NumericalPropagator, third_body_gravity
from oure.risk.foster import MonteCarloSampler


def test_third_body_gravity():
    pos = np.array([7000.0, 0.0, 0.0])
    epoch = datetime.now(UTC)
    acc = third_body_gravity(pos, epoch)
    assert acc.shape == (3,)


def test_numerical_vectorized_third_body():
    prop = NumericalPropagator(use_third_body=True)
    states = np.array(
        [[7000.0, 0.0, 0.0, 0.0, 7.5, 0.0], [7100.0, 0.0, 0.0, 0.0, 7.4, 0.0]]
    )
    epoch = datetime.now(UTC)
    res = prop.propagate_many_to(states, epoch, epoch + timedelta(seconds=10.0))
    assert res.shape == (2, 6)


def test_compute_tle_quality():
    record = TLERecord(
        sat_id="12345",
        name="TEST",
        line1="",
        line2="",
        epoch=datetime.now(UTC),
    )
    # LEO
    q1 = compute_tle_quality(record, 300.0)
    # MEO
    q2 = compute_tle_quality(record, 600.0)
    # GEO
    q3 = compute_tle_quality(record, 1000.0)

    assert 0.0 <= q1 <= 1.0
    assert 0.0 <= q2 <= 1.0
    assert 0.0 <= q3 <= 1.0


def test_monte_carlo_sampler():
    b_miss = np.array([0.0, 0.0])
    C_2d = np.diag([1.0, 1.0])
    pc = MonteCarloSampler.compute_pc(b_miss, C_2d, 0.02, n_samples=1000)
    assert isinstance(pc, float)
    assert 0.0 <= pc <= 1.0
