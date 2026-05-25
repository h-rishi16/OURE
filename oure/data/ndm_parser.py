"""
OURE Data Ingestion Layer - CCSDS NDM Parser
============================================
Handles Orbit Parameter Messages (OPM) and Orbit Ephemeris Messages (OEM).
"""

from __future__ import annotations

import logging
from datetime import UTC

import numpy as np

from oure.core.models import CovarianceMatrix, StateVector

logger = logging.getLogger("oure.data.ndm_parser")


class NDMParser:
    """
    Parses CCSDS NDM files (OPM, OEM) using the ccsds-ndm-py library.
    """

    @staticmethod
    def parse_opm(file_path: str) -> tuple[StateVector, CovarianceMatrix | None]:
        """
        Extracts the StateVector and CovarianceMatrix (if present) from an OPM file.
        """
        import ccsds_ndm
        from ccsds_ndm import Opm

        msg = ccsds_ndm.from_file(file_path)
        if not isinstance(msg, Opm):
            raise ValueError(f"Expected OPM file, got {type(msg).__name__}")

        segment = msg.segments[0]
        metadata = segment.metadata
        data = segment.data

        sat_id = (
            getattr(metadata, "object_id", None)
            or getattr(metadata, "object_name", None)
            or "UNKNOWN"
        )

        # State vector
        sv = data.state_vector
        r = np.array([sv.x, sv.y, sv.z])
        v = np.array([sv.x_dot, sv.y_dot, sv.z_dot])

        from dateutil.parser import parse as parse_date

        epoch_str = str(sv.epoch)
        # Handle "Z" suffix for UTC
        if epoch_str.endswith("Z"):
            epoch_str = epoch_str[:-1] + "+00:00"
        epoch = parse_date(epoch_str)
        if epoch.tzinfo is None:
            epoch = epoch.replace(tzinfo=UTC)

        state = StateVector(r=r, v=v, epoch=epoch, sat_id=sat_id)

        # Covariance Matrix (Optional)
        cov = None
        if data.covariance_matrix is not None:
            c = data.covariance_matrix
            matrix = np.zeros((6, 6))
            try:
                matrix[0, 0] = c.CX_X
                matrix[1, 0] = c.CY_X
                matrix[1, 1] = c.CY_Y
                matrix[2, 0] = c.CZ_X
                matrix[2, 1] = c.CZ_Y
                matrix[2, 2] = c.CZ_Z
                matrix[3, 0] = c.CX_DOT_X
                matrix[3, 1] = c.CX_DOT_Y
                matrix[3, 2] = c.CX_DOT_Z
                matrix[3, 3] = c.CX_DOT_X_DOT
                matrix[4, 0] = c.CY_DOT_X
                matrix[4, 1] = c.CY_DOT_Y
                matrix[4, 2] = c.CY_DOT_Z
                matrix[4, 3] = c.CY_DOT_X_DOT
                matrix[4, 4] = c.CY_DOT_Y_DOT
                matrix[5, 0] = c.CZ_DOT_X
                matrix[5, 1] = c.CZ_DOT_Y
                matrix[5, 2] = c.CZ_DOT_Z
                matrix[5, 3] = c.CZ_DOT_X_DOT
                matrix[5, 4] = c.CZ_DOT_Y_DOT
                matrix[5, 5] = c.CZ_DOT_Z_DOT

                # Make symmetric
                for i in range(6):
                    for j in range(i + 1, 6):
                        matrix[i, j] = matrix[j, i]

                cov = CovarianceMatrix(matrix=matrix, epoch=epoch, sat_id=sat_id)
            except AttributeError as e:
                logger.warning(f"Could not parse OPM covariance: {e}")

        return state, cov

    @staticmethod
    def parse_oem(file_path: str) -> list[StateVector]:
        """
        Extracts a time series of StateVectors from an OEM file.
        """
        import ccsds_ndm
        from ccsds_ndm import Oem
        from dateutil.parser import parse as parse_date

        msg = ccsds_ndm.from_file(file_path)
        if not isinstance(msg, Oem):
            raise ValueError(f"Expected OEM file, got {type(msg).__name__}")

        states = []
        for segment in msg.segments:
            metadata = segment.metadata
            sat_id = (
                getattr(metadata, "object_id", None)
                or getattr(metadata, "object_name", None)
                or "UNKNOWN"
            )

            # state_vector in Oem is a list of StateVectorAcc objects
            for sv_acc in segment.data.state_vector:
                epoch_str = str(sv_acc.epoch)
                if epoch_str.endswith("Z"):
                    epoch_str = epoch_str[:-1] + "+00:00"
                epoch = parse_date(epoch_str)
                if epoch.tzinfo is None:
                    epoch = epoch.replace(tzinfo=UTC)

                r = np.array([sv_acc.x, sv_acc.y, sv_acc.z])
                v = np.array([sv_acc.x_dot, sv_acc.y_dot, sv_acc.z_dot])
                states.append(StateVector(r=r, v=v, epoch=epoch, sat_id=sat_id))

        return states
