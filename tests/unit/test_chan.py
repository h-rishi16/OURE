import numpy as np

from oure.risk.chan import ChanPcCalculator


def test_chan_calculator_basic():
    # 1 km hard body radius
    calc = ChanPcCalculator(hard_body_radius_km=1.0)

    # Isotropic covariance: sigma_x = 2 km, sigma_z = 2 km
    C = np.array([[4.0, 0.0], [0.0, 4.0]])

    # Miss distance: 2 km on x-axis
    b = np.array([2.0, 0.0])

    pc = calc.compute(b, C)

    assert 0.0 < pc < 1.0

    # Let's compare to a known rough analytical value or Foster
    from oure.risk.foster import FosterPcCalculator

    foster_calc = FosterPcCalculator(hard_body_radius_km=1.0)
    pc_foster = foster_calc.compute(b, C)

    # Chan and Foster should be extremely close for isotropic covariance
    np.testing.assert_allclose(pc, pc_foster, rtol=1e-3, atol=1e-4)


def test_chan_calculator_zero_det():
    calc = ChanPcCalculator(hard_body_radius_km=1.0)
    # Singular covariance
    C = np.zeros((2, 2))
    b = np.array([2.0, 0.0])

    pc = calc.compute(b, C)
    assert pc == 0.0
