import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from oure.core.models import (
    ConjunctionEvent,
    CovarianceMatrix,
    OptimizationResult,
    StateVector,
)
from oure.reporting.pdf_report import ConjunctionReportGenerator


def test_pdf_report_generation():
    epoch = datetime.now(UTC)
    state1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), epoch, "123")
    state2 = StateVector(np.array([7000.5, 0, 0]), np.array([0, -7.5, 0]), epoch, "456")
    cov1 = CovarianceMatrix(np.eye(6), epoch, "123")
    cov2 = CovarianceMatrix(np.eye(6), epoch, "456")

    event = ConjunctionEvent(
        primary_id="123",
        secondary_id="456",
        tca=epoch,
        miss_distance_km=0.5,
        relative_velocity_km_s=15.0,
        primary_state=state1,
        secondary_state=state2,
        primary_covariance=cov1,
        secondary_covariance=cov2,
    )

    maneuver = OptimizationResult(
        optimal_dv_km_s=np.array([0.001, 0.0, 0.0]),
        final_pc=1e-6,
        iterations=5,
        success=True,
        message="OK",
        burn_epoch=epoch,
        fuel_cost_kg=0.5,
        station_keeping_ok=True,
    )

    generator = ConjunctionReportGenerator()

    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
        temp_path = Path(f.name)

    try:
        # Generate without maneuver
        generator.generate(event, None, temp_path)
        assert temp_path.exists()
        assert temp_path.stat().st_size > 0

        # Generate with maneuver
        generator.generate(event, maneuver, temp_path)
        assert temp_path.exists()
        assert temp_path.stat().st_size > 0

    finally:
        if temp_path.exists():
            os.unlink(temp_path)
