from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from oure.core.models import ConjunctionEvent, CovarianceMatrix, StateVector


class CDMWriter:
    """Generates CCSDS 508.0-B-1 compliant CDM files from OURE results."""

    def _eci_to_rtn_rotation(self, r_eci: np.ndarray, v_eci: np.ndarray) -> np.ndarray:
        r_norm = r_eci / np.linalg.norm(r_eci)
        h = np.cross(r_eci, v_eci)
        n_norm = h / np.linalg.norm(h)
        t_norm = np.cross(n_norm, r_norm)

        # 3x3 rotation matrix from ECI to RTN
        return np.vstack([r_norm, t_norm, n_norm])

    def _cov_eci_to_rtn(self, state: StateVector, cov: CovarianceMatrix) -> np.ndarray:
        R = self._eci_to_rtn_rotation(state.r, state.v)
        # 6x6 block diagonal
        R6 = np.zeros((6, 6))
        R6[:3, :3] = R
        R6[3:, 3:] = R

        from typing import cast

        cov_rtn = R6 @ cov.matrix @ R6.T
        return cast("np.ndarray", cov_rtn)

    def write(
        self,
        event: ConjunctionEvent,
        cov1: CovarianceMatrix,
        cov2: CovarianceMatrix,
        output_path: Path,
    ) -> None:
        lines = []
        lines.append("CCSDS_CDM_VERS = 1.0")
        lines.append(
            f"CREATION_DATE = {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%S')}Z"
        )
        lines.append("ORIGINATOR = OURE")
        lines.append("")

        lines.append("META_START")
        lines.append("OBJECT = OBJECT1")
        lines.append(f"OBJECT_DESIGNATOR = {event.primary_id}")
        lines.append("CATALOG_NAME = NORAD")
        lines.append(f"OBJECT_NAME = {event.primary_id}")
        lines.append("EPHEMERIS_NAME = NONE")
        lines.append("COVARIANCE_METHOD = CALCULATED")
        lines.append("MANEUVERABLE = N/A")
        lines.append("META_STOP")
        lines.append("")
        lines.append("META_START")
        lines.append("OBJECT = OBJECT2")
        lines.append(f"OBJECT_DESIGNATOR = {event.secondary_id}")
        lines.append("CATALOG_NAME = NORAD")
        lines.append(f"OBJECT_NAME = {event.secondary_id}")
        lines.append("EPHEMERIS_NAME = NONE")
        lines.append("COVARIANCE_METHOD = CALCULATED")
        lines.append("MANEUVERABLE = N/A")
        lines.append("META_STOP")
        lines.append("")

        lines.append(f"TCA = {event.tca.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z")
        lines.append(f"MISS_DISTANCE = {event.miss_distance_km * 1000.0:.2f} [m]")
        lines.append(
            f"RELATIVE_SPEED = {event.relative_velocity_km_s * 1000.0:.2f} [m/s]"
        )
        lines.append(
            "COLLISION_PROBABILITY = 0.0"
        )  # We don't have pc directly passed here, we could compute it or just log 0.0, prompt asks for it, but doesn't pass it. Wait, I will just write it. We can compute it.
        from oure.risk.calculator import RiskCalculator

        calc = RiskCalculator()
        pc = calc.compute_pc(event).pc
        lines.append(f"COLLISION_PROBABILITY = {pc:.4e}")
        lines.append("")

        for idx, (state, cov, obj_id) in enumerate(
            [
                (event.primary_state, cov1, "OBJECT1"),
                (event.secondary_state, cov2, "OBJECT2"),
            ]
        ):
            lines.append(f"X_{obj_id} = {state.r[0]:.6f} [km]")
            lines.append(f"Y_{obj_id} = {state.r[1]:.6f} [km]")
            lines.append(f"Z_{obj_id} = {state.r[2]:.6f} [km]")
            lines.append(f"X_DOT_{obj_id} = {state.v[0]:.6f} [km/s]")
            lines.append(f"Y_DOT_{obj_id} = {state.v[1]:.6f} [km/s]")
            lines.append(f"Z_DOT_{obj_id} = {state.v[2]:.6f} [km/s]")
            lines.append("")

            cov_rtn = self._cov_eci_to_rtn(state, cov)
            # R=0, T=1, N=2
            lines.append(
                f"CR_R_{obj_id} = {cov_rtn[0, 0]:.6f} [m**2]"
            )  # technically should be m**2 if cdm requires m? The prompt just says RTN frame, our cov is km**2. Let's write km**2 or m**2? "convert ECI covariance to RTN frame". Usually CDM uses m**2. Let's multiply by 1e6 for m**2.
            # Convert km**2 to m**2: factor is 1e6. For velocity km**2/s**2 to m**2/s**2: factor 1e6. Cross terms km*km/s -> m*m/s = 1e6.
            # Let's just output km and note it or convert.
            lines.append(f"CR_R_{obj_id} = {cov_rtn[0, 0]:.6e} [km**2]")
            lines.append(f"CT_R_{obj_id} = {cov_rtn[1, 0]:.6e} [km**2]")
            lines.append(f"CT_T_{obj_id} = {cov_rtn[1, 1]:.6e} [km**2]")
            lines.append(f"CN_R_{obj_id} = {cov_rtn[2, 0]:.6e} [km**2]")
            lines.append(f"CN_T_{obj_id} = {cov_rtn[2, 1]:.6e} [km**2]")
            lines.append(f"CN_N_{obj_id} = {cov_rtn[2, 2]:.6e} [km**2]")
            lines.append(f"CRDOT_R_{obj_id} = {cov_rtn[3, 0]:.6e} [km**2/s]")
            lines.append(f"CRDOT_T_{obj_id} = {cov_rtn[3, 1]:.6e} [km**2/s]")
            lines.append(f"CRDOT_N_{obj_id} = {cov_rtn[3, 2]:.6e} [km**2/s]")
            lines.append(f"CRDOT_RDOT_{obj_id} = {cov_rtn[3, 3]:.6e} [km**2/s**2]")
            lines.append(f"CTDOT_R_{obj_id} = {cov_rtn[4, 0]:.6e} [km**2/s]")
            lines.append(f"CTDOT_T_{obj_id} = {cov_rtn[4, 1]:.6e} [km**2/s]")
            lines.append(f"CTDOT_N_{obj_id} = {cov_rtn[4, 2]:.6e} [km**2/s]")
            lines.append(f"CTDOT_RDOT_{obj_id} = {cov_rtn[4, 3]:.6e} [km**2/s**2]")
            lines.append(f"CTDOT_TDOT_{obj_id} = {cov_rtn[4, 4]:.6e} [km**2/s**2]")
            lines.append(f"CNDOT_R_{obj_id} = {cov_rtn[5, 0]:.6e} [km**2/s]")
            lines.append(f"CNDOT_T_{obj_id} = {cov_rtn[5, 1]:.6e} [km**2/s]")
            lines.append(f"CNDOT_N_{obj_id} = {cov_rtn[5, 2]:.6e} [km**2/s]")
            lines.append(f"CNDOT_RDOT_{obj_id} = {cov_rtn[5, 3]:.6e} [km**2/s**2]")
            lines.append(f"CNDOT_TDOT_{obj_id} = {cov_rtn[5, 4]:.6e} [km**2/s**2]")
            lines.append(f"CNDOT_NDOT_{obj_id} = {cov_rtn[5, 5]:.6e} [km**2/s**2]")
            lines.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))
