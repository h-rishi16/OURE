from oure.physics.sgp4_propagator import SGP4Propagator


def test_base_propagate_sequence(sample_tle, dummy_state):
    base_prop = SGP4Propagator(sample_tle)
    epochs = [dummy_state.epoch, dummy_state.epoch]
    results = base_prop.propagate_sequence(dummy_state, epochs)
    assert len(results) == 2
