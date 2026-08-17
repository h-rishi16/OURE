"""
OURE Risk Calculation - Alert Classifier
========================================
"""

from __future__ import annotations

from oure.core.models import RiskResult


class AlertClassifier:
    """
    Classifies a RiskResult into a warning level.
    """

    def __init__(self, red_threshold: float = 1e-3, yellow_threshold: float = 1e-5):
        self.red_threshold = red_threshold
        self.yellow_threshold = yellow_threshold

    def classify(self, result: RiskResult) -> str:
        """
        Classifies the risk result and returns a warning level string.
        Also detects probability dilution (false-confidence theorem).
        """
        if result.pc >= self.red_threshold:
            return "RED"
        elif result.pc >= self.yellow_threshold:
            return "YELLOW"
        else:
            # Detect probability dilution (False-Confidence Theorem)
            # If standard Pc is low, but the Alfano upper bound is very high,
            # it means the low Pc is purely an artifact of huge covariance uncertainty.
            if result.max_pc >= self.red_threshold:
                return "DILUTION_WARNING"
            return "GREEN"
