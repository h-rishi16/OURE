from datetime import UTC, datetime

import numpy as np

from oure.core.models import StateVector
from oure.data.oem import OEMWriter


def test_oem_writer():
    states = [
        StateVector(
            r=np.array([7000.0, 0.0, 0.0]),
            v=np.array([0.0, 7.5, 0.0]),
            epoch=datetime(2026, 5, 27, 10, 0, 0, tzinfo=UTC),
            sat_id="25544",
        ),
        StateVector(
            r=np.array([7000.0, 100.0, 0.0]),
            v=np.array([-1.0, 7.5, 0.0]),
            epoch=datetime(2026, 5, 27, 10, 5, 0, tzinfo=UTC),
            sat_id="25544",
        ),
    ]

    oem_str = OEMWriter.write(states)

    # Assert header and metadata
    assert "CCSDS_OEM_VERS = 2.0" in oem_str
    assert "OBJECT_NAME          = SAT_25544" in oem_str
    assert "START_TIME           = 2026-05-27T10:00:00+00:00" in oem_str

    # Assert data lines
    assert (
        "2026-05-27T10:00:00+00:00 7000.000000 0.000000 0.000000 0.000000 7.500000 0.000000"
        in oem_str
    )
    assert (
        "2026-05-27T10:05:00+00:00 7000.000000 100.000000 0.000000 -1.000000 7.500000 0.000000"
        in oem_str
    )
