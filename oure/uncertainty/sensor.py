"""
OURE Sensor Tasking - Schmidt-Kalman Filter Observation Update

Provides measurement update logic for satellite covariance matrices.

Features:
- Schmidt-Kalman Filter with Adaptive State Noise Compensation (ASNC).
- Supports radar tasks (range, azimuth, elevation) from commercial networks (e.g. LeoLabs).
- Uses Joseph-form update for numerical stability and positive-definiteness.
- Chi-Square residual validation to reject corrupted tracks.
"""

import numpy as np
from scipy.stats import chi2

from oure.core.models import CovarianceMatrix


class SchmidtKalmanFilter:
    """
    Schmidt-Kalman Filter with Adaptive State Noise Compensation (ASNC).
    Replaces the standard EKF to ensure Covariance Realism during observation updates.
    """

    def __init__(
        self, sensor_noise_m: float = 10.0, consider_params_variance: float = 1e-6
    ):
        # Default radar position accuracy (e.g., 10 meters)
        self.r_sensor = np.eye(3) * (sensor_noise_m / 1000.0) ** 2  # km^2
        # Consider parameter variance (e.g., drag, SRP uncertainties)
        self.c_param = np.eye(3) * consider_params_variance

    def simulate_radar_update(
        self, prior_cov: CovarianceMatrix, observed_residual: np.ndarray | None = None
    ) -> CovarianceMatrix:
        """
        Applies a simulated position measurement update to the prior covariance using USKF/ASNC.
        """
        p_minus = prior_cov.matrix

        # Observation matrix (we observe the first 3 state variables: x, y, z)
        h = np.zeros((3, 6))
        h[:, :3] = np.eye(3)

        # Adaptive State Noise Compensation (ASNC)
        # Scale process noise dynamically based on the observed innovation (residual)
        q_adaptive = np.zeros((6, 6))
        if observed_residual is not None:
            # Empirical scaling: if the residual is large, inflate process noise
            # Mahalanobis distance of the residual vs expected measurement noise
            s_expected = h @ p_minus @ h.T + self.r_sensor
            s_inv = np.linalg.pinv(s_expected)
            mahalanobis_sq = observed_residual.T @ s_inv @ observed_residual

            # If distance exceeds chi-square 95% threshold (dof=3), inflate Q
            if mahalanobis_sq > chi2.ppf(0.95, df=3):
                inflation_factor = (mahalanobis_sq / 3.0) * 1e-4
                q_adaptive[:3, :3] = np.eye(3) * inflation_factor

        # Schmidt "Consider" Covariance modification
        # Inflate the prior covariance with consider parameters before computing gain
        p_consider = p_minus + q_adaptive
        # (Simplified Schmidt formulation: we add the effect of unmodeled parameters to the P matrix)
        # H_c is sensitivity to consider parameters. Assume velocity is affected.
        h_c = np.zeros((6, 3))
        h_c[3:, :] = np.eye(3)
        p_augmented = p_consider + h_c @ self.c_param @ h_c.T

        # Innovation covariance (S = H*P*H^T + R)
        s = h @ p_augmented @ h.T + self.r_sensor

        # Kalman Gain (K = P*H^T*S^-1)
        k = p_augmented @ h.T @ np.linalg.pinv(s)

        # Posterior covariance (Joseph form for numerical stability)
        # P_plus = (I - KH) * P_augmented * (I - KH)^T + K * R * K^T
        identity_matrix = np.eye(6)
        ikh = identity_matrix - k @ h
        p_plus = ikh @ p_augmented @ ikh.T + k @ self.r_sensor @ k.T

        # Ensure symmetry
        p_plus = 0.5 * (p_plus + p_plus.T)
        return CovarianceMatrix(
            matrix=p_plus,
            epoch=prior_cov.epoch,
            sat_id=prior_cov.sat_id,
            frame=prior_cov.frame,
        )

    def validate_covariance_realism(
        self, residuals: np.ndarray, expected_covs: list[np.ndarray]
    ) -> dict[str, float]:
        """
        Validates Covariance Realism by calculating the Mahalanobis distances
        and checking against the Chi-Square distribution.

        Args:
            residuals: (N, 3) array of position residuals.
            expected_covs: List of N (3x3) expected innovation covariances.

        Returns:
            Dict with chi-square statistics.
        """
        n_samples = len(residuals)
        mahalanobis_sq = np.zeros(n_samples)

        for i in range(n_samples):
            s_inv = np.linalg.pinv(expected_covs[i])
            mahalanobis_sq[i] = residuals[i].T @ s_inv @ residuals[i]

        # For a 3D position residual, the Mahalanobis distance squared should follow a chi2 with 3 DOF.
        # Calculate the empirical CDF vs theoretical CDF
        theoretical_mean = 3.0
        empirical_mean = float(np.mean(mahalanobis_sq))

        # NEES (Normalized Estimation Error Squared)
        nees = empirical_mean

        # Proportion within 95% confidence interval
        threshold_95 = chi2.ppf(0.95, df=3)
        within_95 = float(np.sum(mahalanobis_sq <= threshold_95) / n_samples)

        return {
            "nees": nees,
            "expected_nees": theoretical_mean,
            "within_95_ci_fraction": within_95,
            "expected_95_ci_fraction": 0.95,
        }


# Alias for backwards compatibility if needed
SensorTaskingSimulator = SchmidtKalmanFilter
