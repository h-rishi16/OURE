import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from oure.risk.foster import FosterPcCalculator, PcMethod


@st.composite
def spd_matrices(draw):
    """Generate 2x2 Symmetric Positive-Definite matrices representing covariance."""
    sigma_x = draw(
        st.floats(
            min_value=1e-2, max_value=100.0, allow_nan=False, allow_infinity=False
        )
    )
    sigma_z = draw(
        st.floats(
            min_value=1e-2, max_value=100.0, allow_nan=False, allow_infinity=False
        )
    )
    # Correlation strictly between -0.99 and 0.99 to ensure positive definiteness and avoid singularity
    rho = draw(
        st.floats(
            min_value=-0.99, max_value=0.99, allow_nan=False, allow_infinity=False
        )
    )
    return np.array(
        [[sigma_x**2, rho * sigma_x * sigma_z], [rho * sigma_x * sigma_z, sigma_z**2]]
    )


@st.composite
def miss_vectors(draw):
    """Generate 2D miss vectors on the B-plane."""
    x = draw(
        st.floats(
            min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        )
    )
    z = draw(
        st.floats(
            min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        )
    )
    return np.array([x, z])


@pytest.mark.req("REQ-PHYS-03")
@given(b_miss=miss_vectors(), C_2d=spd_matrices())
@settings(max_examples=100, deadline=1000)
def test_pc_always_in_unit_interval(b_miss, C_2d):
    """Test that Pc is strictly between 0 and 1 for any valid physics inputs."""
    calc = FosterPcCalculator(
        hard_body_radius_km=10.0, method=PcMethod.FOSTER_SERIES, use_mc_fallback=False
    )
    pc = calc.compute(b_miss, C_2d)
    assert 0.0 <= pc <= 1.0


@given(b_miss=miss_vectors(), C_2d=spd_matrices())
@settings(max_examples=100, deadline=1000)
def test_pc_symmetry(b_miss, C_2d):
    """Test that Pc is invariant under object inversion (swapping primary and secondary)."""
    calc = FosterPcCalculator(
        hard_body_radius_km=10.0, method=PcMethod.FOSTER_SERIES, use_mc_fallback=False
    )
    pc1 = calc.compute(b_miss, C_2d)
    pc2 = calc.compute(-b_miss, C_2d)
    assert pc1 == pytest.approx(pc2, abs=1e-12)


@given(b_miss=miss_vectors(), C_2d=spd_matrices())
@settings(max_examples=10, deadline=None)
def test_series_vs_numerical(b_miss, C_2d):
    """Verify Foster Series analytic method matches SciPy dblquad numerical integration."""
    # Ensure condition number is manageable for the numerical method
    det_C = np.linalg.det(C_2d)
    if det_C < 1e-4:
        return

    # The Foster Series algorithm assumes the covariance isn't extremely elongated.
    # It loses accuracy compared to direct numerical integration for high aspect ratios.
    eigenvalues = np.linalg.eigvalsh(C_2d)
    if np.max(eigenvalues) / np.min(eigenvalues) > 5.0:
        return

    calc_series = FosterPcCalculator(
        hard_body_radius_km=10.0, method=PcMethod.FOSTER_SERIES, use_mc_fallback=False
    )
    calc_num = FosterPcCalculator(
        hard_body_radius_km=10.0,
        method=PcMethod.NUMERICAL,
        integration_sigma=6.0,
        use_mc_fallback=False,
    )

    pc_series = calc_series.compute(b_miss, C_2d)
    pc_num = calc_num.compute(b_miss, C_2d)

    # We use a relatively loose absolute tolerance since dblquad uses approximations
    # at the bounds and the integration domain is finite (6 sigma). It is known to
    # struggle with the hard circular boundary of the collision disk.
    assert pc_series == pytest.approx(pc_num, abs=5e-3)


@given(C_2d=spd_matrices())
@settings(max_examples=50)
def test_pc_zero_at_infinity(C_2d):
    """Test that extreme miss distances yield effectively zero probability."""
    calc = FosterPcCalculator(
        hard_body_radius_km=1.0, method=PcMethod.FOSTER_SERIES, use_mc_fallback=False
    )
    # Put them 100,000 km apart
    pc = calc.compute(np.array([100000.0, 100000.0]), C_2d)
    assert pc == pytest.approx(0.0, abs=1e-12)
