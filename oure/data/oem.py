"""
CCSDS OEM (Orbit Ephemeris Message) Writer
==========================================
Exports sequences of StateVectors to the industry standard CCSDS OEM KVN format.
"""

from datetime import UTC, datetime
from typing import List

from oure.core.models import StateVector


class OEMWriter:
    """Writes ephemeris data to CCSDS OEM format."""

    @staticmethod
    def write(states: List[StateVector], originator: str = "OURE") -> str:
        """
        Converts a list of StateVectors into a CCSDS OEM string.

        Args:
            states: A time-ordered list of StateVector instances for a single satellite.
            originator: The originating organization or software.

        Returns:
            A string containing the KVN-formatted OEM file.
        """
        if not states:
            raise ValueError("State vector list is empty.")

        sat_id = states[0].sat_id
        start_time = states[0].epoch.isoformat()
        stop_time = states[-1].epoch.isoformat()
        creation_date = datetime.now(UTC).isoformat()

        lines = [
            "CCSDS_OEM_VERS = 2.0",
            f"CREATION_DATE  = {creation_date}",
            f"ORIGINATOR     = {originator}",
            "",
            "META_START",
            f"OBJECT_NAME          = SAT_{sat_id}",
            f"OBJECT_ID            = {sat_id}",
            "CENTER_NAME          = EARTH",
            "REF_FRAME            = EME2000",
            "TIME_SYSTEM          = UTC",
            f"START_TIME           = {start_time}",
            f"USEABLE_START_TIME   = {start_time}",
            f"USEABLE_STOP_TIME    = {stop_time}",
            f"STOP_TIME            = {stop_time}",
            "META_STOP",
            "",
        ]

        # Ephemeris Data lines
        for state in states:
            t = state.epoch.isoformat()
            r = state.r
            v = state.v
            # Format: YYYY-MM-DDThh:mm:ss.ddd X Y Z X_DOT Y_DOT Z_DOT
            data_line = (
                f"{t} {r[0]:.6f} {r[1]:.6f} {r[2]:.6f} {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}"
            )
            lines.append(data_line)

        return "\n".join(lines) + "\n"
