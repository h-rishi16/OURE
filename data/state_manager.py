import numpy as np


def align_epochs(target_epoch, satellite_states):
    """
    Aligns a list of satellite states to a target epoch using polynomial interpolation.
    Expects satellite_states to be a list of dictionaries, each containing:
    - 'epoch': float (timestamp)
    - 'state': np.array of shape (6,) -> [x, y, z, vx, vy, vz]

    Returns a new list of dictionaries with updated 'epoch' and 'state'
    """
    aligned_states = []
    target_t = target_epoch

    for sat in satellite_states:
        # Very basic interpolation for demonstration
        # For a single state, we would need multiple past states for true polynomial interpolation.
        # But assuming we just linearly project using velocity if only 1 point is given,
        # or if we had a history we could use numpy.polyfit.
        # Since we just have state vector [r, v], we can do a simple linear or Taylor series projection.
        # Here we do a simple 1st order projection (r = r0 + v0 * dt)

        t0 = sat["epoch"]
        dt = target_t - t0

        r0 = sat["state"][:3]
        v0 = sat["state"][3:]

        r_new = r0 + v0 * dt
        v_new = v0  # Assuming constant velocity for this simple mock

        aligned_states.append(
            {
                "epoch": target_t,
                "state": np.concatenate((r_new, v_new)),
                "id": sat.get("id"),
            }
        )

    return aligned_states
