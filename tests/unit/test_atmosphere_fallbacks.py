from datetime import UTC, datetime
from unittest.mock import patch

import numpy as np

from oure.core import constants
from oure.physics.atmosphere import AtmosphereType, AtmosphericModel


def test_atmosphere_import_error_fallback():
    model = AtmosphericModel(
        solar_flux=150.0, model_type=AtmosphereType.NASA_MSFC_JACCHIA
    )

    pos = np.array([constants.R_EARTH_KM + 400.0, 0, 0])
    epoch = datetime.now(UTC)

    import sys

    # Mock ImportError on nrlmsise00
    with patch.dict(sys.modules, {"nrlmsise00": None}):
        # Test scalar NASA MSFC fallback
        rho = model.get_density(pos, epoch)
        assert rho > 0

        # Test scalar Standard fallback
        model.model_type = AtmosphereType.STANDARD_EXPONENTIAL
        rho_std = model.get_density(pos, epoch)
        assert rho_std > 0

        # Test vectorized NASA MSFC fallback
        model.model_type = AtmosphereType.NASA_MSFC_JACCHIA
        rho_vec = model.get_density_vectorized(np.array([pos]), [epoch])
        assert len(rho_vec) == 1
        assert rho_vec[0] > 0

        # Test vectorized Standard fallback
        model.model_type = AtmosphereType.STANDARD_EXPONENTIAL
        rho_vec_std = model.get_density_vectorized(np.array([pos]), [epoch])
        assert len(rho_vec_std) == 1
        assert rho_vec_std[0] > 0
