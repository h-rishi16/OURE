import os
import tempfile
from datetime import UTC, datetime

import numpy as np
import polars as pl

from oure.core.models import StateVector
from oure.data.fast_io import EphemerisIO


def test_to_dataframe():
    epoch = datetime(2025, 5, 9, 12, 0, tzinfo=UTC)
    s1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), epoch, "123")
    s2 = StateVector(np.array([7000.5, 0, 0]), np.array([0, -7.5, 0]), epoch, "456")

    df = EphemerisIO.to_dataframe([s1, s2])
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 2
    assert list(df["sat_id"]) == ["123", "456"]
    assert list(df["x"]) == [7000.0, 7000.5]


def test_from_dataframe():
    epoch = datetime(2025, 5, 9, 12, 0, tzinfo=UTC)
    s1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), epoch, "123")

    df = EphemerisIO.to_dataframe([s1])
    states = EphemerisIO.from_dataframe(df)

    assert len(states) == 1
    assert states[0].sat_id == "123"
    assert np.array_equal(states[0].r, np.array([7000.0, 0, 0]))
    assert states[0].epoch == epoch


def test_empty_dataframe():
    df = EphemerisIO.to_dataframe([])
    assert len(df) == 0
    states = EphemerisIO.from_dataframe(df)
    assert len(states) == 0


def test_parquet_save_load():
    epoch = datetime(2025, 5, 9, 12, 0, tzinfo=UTC)
    s1 = StateVector(np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), epoch, "123")

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_path = f.name

    try:
        EphemerisIO.save_parquet([s1], temp_path)
        assert os.path.exists(temp_path)

        loaded = EphemerisIO.load_parquet(temp_path)
        assert len(loaded) == 1
        assert loaded[0].sat_id == "123"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
