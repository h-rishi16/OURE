"""
OURE Data Ingestion - High Speed I/O
====================================
Utilizes Polars and Astropy v7.2+ for massive performance gains
when converting ephemeris data to and from DataFrames.
"""

from __future__ import annotations

import logging
from datetime import UTC

import numpy as np
import polars as pl

from oure.core.models import StateVector

logger = logging.getLogger("oure.data.fast_io")


class EphemerisIO:
    """
    Provides high-speed DataFrame conversions for StateVectors.
    Replaces slow list comprehensions with vectorized Polars operations.
    """

    @staticmethod
    def to_dataframe(states: list[StateVector]) -> pl.DataFrame:
        """
        Converts a list of StateVectors into a Polars DataFrame rapidly.
        """
        if not states:
            return pl.DataFrame()

        # Extract data into dictionary of columns for fast Polars construction
        data = {
            "sat_id": [s.sat_id for s in states],
            "epoch": [s.epoch for s in states],
            "x": [s.r[0] for s in states],
            "y": [s.r[1] for s in states],
            "z": [s.r[2] for s in states],
            "vx": [s.v[0] for s in states],
            "vy": [s.v[1] for s in states],
            "vz": [s.v[2] for s in states],
        }

        df = pl.DataFrame(data)
        return df

    @staticmethod
    def from_dataframe(df: pl.DataFrame) -> list[StateVector]:
        """
        Converts a Polars DataFrame back into a list of StateVectors.
        """
        if df.is_empty():
            return []

        # Convert to dictionary of arrays for fast object instantiation
        data_dict = df.to_dict(as_series=False)

        sat_ids = data_dict["sat_id"]
        epochs = data_dict["epoch"]

        xs = np.array(data_dict["x"])
        ys = np.array(data_dict["y"])
        zs = np.array(data_dict["z"])
        vxs = np.array(data_dict["vx"])
        vys = np.array(data_dict["vy"])
        vzs = np.array(data_dict["vz"])

        n_rows = len(sat_ids)
        states = []
        for i in range(n_rows):
            r = np.array([xs[i], ys[i], zs[i]])
            v = np.array([vxs[i], vys[i], vzs[i]])
            epoch = epochs[i]
            # Ensure UTC timezone
            if epoch.tzinfo is None:
                epoch = epoch.replace(tzinfo=UTC)
            states.append(StateVector(r=r, v=v, epoch=epoch, sat_id=sat_ids[i]))

        return states

    @staticmethod
    def save_parquet(states: list[StateVector], filepath: str) -> None:
        """Saves a list of StateVectors to a high-speed Parquet file."""
        df = EphemerisIO.to_dataframe(states)
        df.write_parquet(filepath)
        logger.info(f"Saved {len(states)} records to {filepath}")

    @staticmethod
    def load_parquet(filepath: str) -> list[StateVector]:
        """Loads a list of StateVectors from a high-speed Parquet file."""
        df = pl.read_parquet(filepath)
        states = EphemerisIO.from_dataframe(df)
        logger.info(f"Loaded {len(states)} records from {filepath}")
        return states
