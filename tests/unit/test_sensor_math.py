from datetime import UTC, datetime

import numpy as np

from oure.core.models import CovarianceMatrix
from oure.uncertainty.sensor import SensorTaskingSimulator


def test_sensor_tasking_simulator():
    prior_cov = CovarianceMatrix(
        matrix=np.eye(6) * 1.0,  # Large uncertainty
        epoch=datetime.now(UTC),
        sat_id="1",
    )

    simulator = SensorTaskingSimulator(sensor_noise_m=10.0)
    posterior_cov = simulator.simulate_radar_update(prior_cov)

    # The position block uncertainty should be much smaller now
    assert np.trace(posterior_cov.matrix[:3, :3]) < np.trace(prior_cov.matrix[:3, :3])
    # Should be close to the sensor noise level (10m = 0.01km -> sigma^2 = 0.0001)
    assert posterior_cov.matrix[0, 0] < 0.01
    assert posterior_cov.is_positive_definite


def test_validate_covariance_realism():
    simulator = SensorTaskingSimulator(sensor_noise_m=10.0)

    residuals = np.random.multivariate_normal(np.zeros(3), np.eye(3), 100)
    expected_covs = [np.eye(3)] * 100

    stats = simulator.validate_covariance_realism(residuals, expected_covs)

    assert "nees" in stats
    assert "within_95_ci_fraction" in stats
    assert stats["expected_nees"] == 3.0
    assert stats["expected_95_ci_fraction"] == 0.95
    assert 0.0 <= stats["within_95_ci_fraction"] <= 1.0
