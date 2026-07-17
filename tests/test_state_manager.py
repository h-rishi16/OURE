import numpy as np

from data.state_manager import align_epochs


def test_align_epochs():
    # Create 1000 mock satellite states
    states = []
    for i in range(1000):
        states.append(
            {
                "id": i,
                "epoch": 0.0,
                "state": np.array(
                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
                ),  # moving 1 km/s along X
            }
        )

    aligned = align_epochs(10.0, states)

    assert len(aligned) == 1000
    assert aligned[0]["epoch"] == 10.0
    assert np.allclose(aligned[0]["state"], np.array([10.0, 0.0, 0.0, 1.0, 0.0, 0.0]))
