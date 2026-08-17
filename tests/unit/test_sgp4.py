from oure.physics.sgp4_propagator import SGP4Propagator


def test_sgp4_base(sample_tle, dummy_state):
    propagator = SGP4Propagator(sample_tle)

    from oure.core.models import StateVector

    # Use TLE epoch to prevent massive orbital decay in SGP4 prediction
    state_at_epoch = StateVector(
        r=dummy_state.r, v=dummy_state.v, epoch=sample_tle.epoch, sat_id="12345"
    )

    propagated_state = propagator.propagate(state_at_epoch, 3600.0)
    assert propagated_state.r.shape == (3,)
    assert propagated_state.v.shape == (3,)

    # Assert the propagated position is within ISS bounds (approx 380 - 430 km)
    alt = propagated_state.altitude_km
    assert 380.0 <= alt <= 440.0


def test_sgp4_propagate_sequence(sample_tle, dummy_state):
    from datetime import timedelta

    from oure.core.models import StateVector

    propagator = SGP4Propagator(sample_tle)
    state_at_epoch = StateVector(
        r=dummy_state.r, v=dummy_state.v, epoch=sample_tle.epoch, sat_id="12345"
    )

    epochs = [sample_tle.epoch + timedelta(seconds=i * 60) for i in range(10)]
    states = propagator.propagate_sequence(state_at_epoch, epochs)

    assert len(states) == 10
    assert states[0].epoch == sample_tle.epoch
    assert states[9].epoch == epochs[-1]

    for s in states:
        assert 380.0 <= s.altitude_km <= 440.0


def test_sgp4_propagate_many_to(sample_tle, dummy_state):
    from datetime import timedelta

    import numpy as np

    propagator = SGP4Propagator(sample_tle)
    # create 100 perturbed states
    N = 100
    r_batch = dummy_state.r + np.random.normal(0, 0.1, (N, 3))
    v_batch = dummy_state.v + np.random.normal(0, 0.001, (N, 3))
    states_6d = np.hstack([r_batch, v_batch])

    target_epoch = sample_tle.epoch + timedelta(seconds=3600)

    propagated_batch = propagator.propagate_many_to(
        states_6d, sample_tle.epoch, target_epoch
    )

    assert propagated_batch.shape == (N, 6)

    # Check physical constraints of the batch propagation
    for i in range(N):
        r_norm = np.linalg.norm(propagated_batch[i, :3])
        alt = r_norm - 6378.137  # R_EARTH_KM
        assert 300.0 <= alt <= 500.0
