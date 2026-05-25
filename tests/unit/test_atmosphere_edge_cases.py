from datetime import UTC, datetime

import numpy as np

from oure.core import constants
from oure.physics.atmosphere import AtmosphereType, AtmosphericModel


def test_nasa_msfc_density_edge_cases():
    model = AtmosphericModel(
        solar_flux=150.0, model_type=AtmosphereType.NASA_MSFC_JACCHIA
    )

    # Test below limit
    val_low = model.get_density(
        np.array([constants.R_EARTH_KM + 100.0, 0, 0]), datetime.now(UTC)
    )
    assert val_low > 0

    # Test above limit
    val_high = model.get_density(
        np.array([constants.R_EARTH_KM + 800.0, 0, 0]), datetime.now(UTC)
    )
    assert val_high > 0


def test_standard_density_edge_cases():
    model = AtmosphericModel(
        solar_flux=150.0, model_type=AtmosphereType.STANDARD_EXPONENTIAL
    )

    # Test exact bounds
    val_200 = model.get_density(
        np.array([constants.R_EARTH_KM + 200.0, 0, 0]), datetime.now(UTC)
    )
    val_700 = model.get_density(
        np.array([constants.R_EARTH_KM + 700.0, 0, 0]), datetime.now(UTC)
    )
    assert val_200 > 0
    assert val_700 > 0

    # Out of bounds should return 1e-14
    val_100 = model.get_density(
        np.array([constants.R_EARTH_KM + 100.0, 0, 0]), datetime.now(UTC)
    )
    assert val_100 > 0


def test_vectorized_edge_cases():
    model = AtmosphericModel(
        solar_flux=150.0, model_type=AtmosphereType.STANDARD_EXPONENTIAL
    )

    positions = np.array(
        [
            [constants.R_EARTH_KM + 100.0, 0, 0],
            [constants.R_EARTH_KM + 450.0, 0, 0],
            [constants.R_EARTH_KM + 800.0, 0, 0],
        ]
    )
    epochs = [datetime.now(UTC)] * 3

    rho = model.get_density_vectorized(positions, epochs)
    assert len(rho) == 3
    assert np.all(rho > 0)

    model_nasa = AtmosphericModel(
        solar_flux=150.0, model_type=AtmosphereType.NASA_MSFC_JACCHIA
    )
    rho_nasa = model_nasa.get_density_vectorized(positions, epochs)
    assert len(rho_nasa) == 3
    assert np.all(rho_nasa > 0)
