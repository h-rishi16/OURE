from oure.physics.factory import PropagatorFactory
from oure.physics.numerical import NumericalPropagator
from oure.physics.sgp4_propagator import SGP4Propagator


def test_factory_build_all_layers(sample_tle):
    prop = PropagatorFactory.build(sample_tle, use_analytical=False)
    assert isinstance(prop, NumericalPropagator)


def test_factory_build_sgp4_only(sample_tle):
    prop = PropagatorFactory.build(sample_tle, use_analytical=True)
    assert isinstance(prop, SGP4Propagator)
