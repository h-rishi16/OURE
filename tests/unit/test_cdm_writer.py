import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from oure.core.models import ConjunctionEvent, CovarianceMatrix, StateVector
from oure.data.cdm_writer import CDMWriter


@pytest.mark.req("REQ-DATA-03")
def test_cdm_writer():
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

    writer = CDMWriter()

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".cdm") as f:
        temp_path = Path(f.name)

    try:
        writer.write(event, cov1, cov2, temp_path)

        assert temp_path.exists()
        content = temp_path.read_text()

        assert "CCSDS_CDM_VERS = 1.0" in content
        assert "OBJECT_DESIGNATOR = 123" in content
        assert "OBJECT_DESIGNATOR = 456" in content
        assert "CR_R_OBJECT1 =" in content
        assert "CR_R_OBJECT2 =" in content

    finally:
        if temp_path.exists():
            os.unlink(temp_path)
