import numpy as np

from oure.core.constants import MU_KM3_S2
from oure.physics.frames import coe2rv_vectorized, rv2coe_vectorized


def test_rv2coe_and_back():
    # Generic 3D elliptical orbit to avoid raan/argp singularities
    r = np.array([[6000.0, 2000.0, 1000.0]])
    v = np.array([[-1.0, 5.0, 4.0]])

    a, ecc, incl, raan, argp, nu = rv2coe_vectorized(r, v, MU_KM3_S2)

    # Check shape
    assert a.shape == (1,)
    assert ecc.shape == (1,)

    # Reconstruct
    r_new, v_new = coe2rv_vectorized(a, ecc, incl, raan, argp, nu, MU_KM3_S2)

    np.testing.assert_allclose(r_new, r, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(v_new, v, rtol=1e-5, atol=1e-5)


def test_multiple_states_vectorized():
    # Batch test for vectorization
    r = np.array(
        [
            [6000.0, 2000.0, 1000.0],
            [10000.0, -5000.0, 2000.0],
            [10000.0, 5000.0, 2000.0],
        ]
    )
    v = np.array([[-1.0, 5.0, 4.0], [-2.0, 3.0, -1.0], [-1.0, 4.0, 5.0]])

    a, ecc, incl, raan, argp, nu = rv2coe_vectorized(r, v)

    r_new, v_new = coe2rv_vectorized(a, ecc, incl, raan, argp, nu)

    np.testing.assert_allclose(r_new, r, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(v_new, v, rtol=1e-5, atol=1e-5)


def test_edge_case_circular_equatorial():
    # Edge case where inclination and eccentricity are near zero
    r = np.array([[7000.0, 0.0, 0.0]])
    v = np.array([[0.0, np.sqrt(MU_KM3_S2 / 7000.0), 0.0]])

    a, ecc, incl, raan, argp, nu = rv2coe_vectorized(r, v)
    assert ecc[0] < 1e-10
    assert incl[0] < 1e-10

    r_new, v_new = coe2rv_vectorized(a, ecc, incl, raan, argp, nu)
    np.testing.assert_allclose(r_new, r, atol=1e-8)
    np.testing.assert_allclose(v_new, v, atol=1e-8)
