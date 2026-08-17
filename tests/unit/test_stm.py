import numpy as np

from oure.uncertainty.stm import STMCalculator


def test_stm_calculator_shape(dummy_state):
    for fidelity in [0, 1, 2]:
        dt = 60.0 if fidelity < 2 else 10.0
        calculator = STMCalculator(fidelity=fidelity)
        stm = calculator.compute(dummy_state, dt)
        assert stm.shape == (6, 6)


def test_stm_identity_at_zero(dummy_state):
    calculator = STMCalculator(fidelity=0)
    stm = calculator.compute(dummy_state, 0.0)
    assert np.allclose(stm, np.eye(6), atol=1e-12)


def test_stm_symplecticity_determinant(dummy_state):
    # Two-body Hamiltonian systems preserve phase space volume (Liouville's theorem)
    # The determinant of the STM must be 1.0
    calculator = STMCalculator(fidelity=0)
    stm = calculator.compute(dummy_state, 120.0)
    assert np.isclose(np.linalg.det(stm), 1.0, atol=1e-5)


def test_stm_transitive_property(dummy_state):
    # STM(t2, t0) = STM(t2, t1) @ STM(t1, t0) (approximate for linear steps)
    calc = STMCalculator(fidelity=0)
    dt1, dt2 = 10.0, 10.0

    # Compute STM from 0 to dt1 + dt2
    stm_full = calc.compute(dummy_state, dt1 + dt2)

    # Compute sequentially
    stm_step1 = calc.compute(dummy_state, dt1)
    # Propagate state to t1 (rough linear propagation for dummy test purposes)
    import copy

    state_t1 = copy.deepcopy(dummy_state)
    # Use object.__setattr__ because the class is frozen
    object.__setattr__(state_t1, "r", state_t1.r + state_t1.v * dt1)
    stm_step2 = calc.compute(state_t1, dt2)

    # Check transitive composition
    stm_composed = stm_step2 @ stm_step1
    # Allow some tolerance due to the rough state propagation
    assert np.allclose(stm_full, stm_composed, atol=1e-1)
