import numpy as np

from oure.risk.alfano import AlfanoPcCalculator


def test_alfano_pc_max_probability():
    calc = AlfanoPcCalculator(hard_body_radius_km=0.02)  # 20m HBR

    # Simple 2D setup:
    # Miss distance is 0.5 km (500m)
    b_miss = np.array([0.5, 0.0])

    # Covariance matrix (not actually used deeply by Alfano's method since it optimizes over sigma,
    # but we pass it anyway for the signature)
    c_2d = np.array([[1.0, 0.0], [0.0, 1.0]])

    pc = calc.compute(b_miss, c_2d)

    # Alfano max probability for d=0.5, r=0.02 should be approx (0.02^2) / (0.5^2 * 2.718) = 0.0004 / 0.6795 = 0.000588
    # Using the exact calculation, let's just make sure it returns a positive probability > 0 and < 1
    assert pc > 0.0001
    assert pc < 0.01


def test_alfano_pc_collision():
    calc = AlfanoPcCalculator(hard_body_radius_km=0.02)
    b_miss = np.array([0.01, 0.0])  # 10m miss distance, smaller than 20m HBR
    c_2d = np.eye(2)
    pc = calc.compute(b_miss, c_2d)
    assert pc == 1.0  # Should be 100% collision if inside HBR
