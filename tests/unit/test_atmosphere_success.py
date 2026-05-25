from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from oure.core import constants
from oure.physics.atmosphere import AtmosphereType, AtmosphericModel


def test_atmosphere_success_import():
    model = AtmosphericModel(
        solar_flux=150.0, model_type=AtmosphereType.NASA_MSFC_JACCHIA
    )

    pos = np.array([constants.R_EARTH_KM + 400.0, 0, 0])
    epoch = datetime.now(UTC)

    import sys

    mock_nrl = MagicMock()
    mock_msise = MagicMock()
    # msise_model returns list of lists where [0][5] is total density
    mock_msise.return_value = [[0, 0, 0, 0, 0, 1.23e-12]]
    mock_nrl.msise_model = mock_msise

    mock_astropy = MagicMock()
    mock_units = MagicMock()
    mock_units.km = 1.0  # Use a float so numpy multiplication works
    mock_units.deg = 1.0
    mock_astropy.units = mock_units

    mock_coord = MagicMock()
    mock_gcrs = MagicMock()
    mock_itrs = MagicMock()

    # Setup the transformation chain
    mock_transformed = MagicMock()
    mock_transformed.spherical.lat.to_value.return_value = 45.0
    mock_transformed.spherical.lon.to_value.return_value = -45.0
    mock_gcrs_inst = MagicMock()
    mock_gcrs_inst.transform_to.return_value = mock_transformed

    mock_gcrs.return_value = mock_gcrs_inst
    mock_coord.GCRS = mock_gcrs
    mock_coord.ITRS = mock_itrs
    mock_coord.CartesianRepresentation = MagicMock()
    mock_astropy.coordinates = mock_coord

    mock_time = MagicMock()
    mock_time.Time = MagicMock()
    mock_astropy.time = mock_time

    modules = {
        "nrlmsise00": mock_nrl,
        "astropy": mock_astropy,
        "astropy.units": mock_units,
        "astropy.coordinates": mock_coord,
        "astropy.time": mock_time,
    }

    with patch.dict(sys.modules, modules):
        # Test scalar NASA MSFC success
        rho = model.get_density(pos, epoch)
        assert rho == pytest.approx(1.23e-12 * 1000.0)

        # Test vectorized NASA MSFC success
        rho_vec = model.get_density_vectorized(np.array([pos]), [epoch])
        assert len(rho_vec) == 1
        assert rho_vec[0] == pytest.approx(1.23e-12 * 1000.0)
