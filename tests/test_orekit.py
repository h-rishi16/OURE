from datetime import UTC, datetime

import pytest

from oure.core.models import TLERecord
from oure.physics.factory import PropagatorFactory


def test_orekit_graceful_fail():
    tle = TLERecord(
        sat_id="25544",
        name="ISS (ZARYA)",
        line1="1 25544U 98067A   26147.12345678  .00012345  00000-0  12345-3 0  9999",
        line2="2 25544  51.6400 123.4567 0001234  90.0000 270.0000 15.50000000123456",
        epoch=datetime(2026, 5, 27, 10, 0, 0, tzinfo=UTC),
    )

    # Orekit is not installed in the PyPI dependencies (intentionally)
    # The factory should raise an ImportError with our custom message when backend="orekit"
    with pytest.raises(ImportError) as exc_info:
        PropagatorFactory.build(tle, backend="orekit")

    assert "The 'orekit' package is not installed." in str(exc_info.value)
    assert "conda install -c conda-forge orekit" in str(exc_info.value)
