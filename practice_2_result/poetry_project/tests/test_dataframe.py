from __future__ import annotations

import pandas as pd
import pytest

from plt_temp import build_dataframe


@pytest.fixture
def sample_hours() -> list[str]:
    return [
        "2024-01-01T12:00",
        "2024-01-01T10:00",
        "2024-01-01T11:00",
    ]


@pytest.fixture
def sample_temps() -> list[float]:
    return [1.0, 3.0, 2.0] 


def test_columns(sample_hours, sample_temps):
    df = build_dataframe(sample_hours, sample_temps)
    assert list(df.columns) == ["time", "temperature_c"]


def test_row_count(sample_hours, sample_temps):
    df = build_dataframe(sample_hours, sample_temps)
    assert len(df) == len(sample_hours) == 3


def test_sorted_by_time(sample_hours, sample_temps):
    df = build_dataframe(sample_hours, sample_temps)
    assert df["time"].is_monotonic_increasing


def test_temperature_matches_time_after_sort(sample_hours, sample_temps):
    df = build_dataframe(sample_hours, sample_temps)
    # 10:00 -> 3.0, 11:00 -> 2.0, 12:00 -> 1.0
    assert df.loc[0, "temperature_c"] == 3.0
    assert df.loc[1, "temperature_c"] == 2.0
    assert df.loc[2, "temperature_c"] == 1.0
    
    expected = {
        pd.Timestamp("2024-01-01T10:00"): 3.0,
        pd.Timestamp("2024-01-01T11:00"): 2.0,
        pd.Timestamp("2024-01-01T12:00"): 1.0,
    }
    for _, row in df.iterrows():
        assert expected[row["time"]] == row["temperature_c"]