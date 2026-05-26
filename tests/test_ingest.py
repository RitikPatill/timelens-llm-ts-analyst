import io
from pathlib import Path

import pandas as pd
import pytest

from timelens.ingest import SeriesMetadata, load_csv

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


def test_returns_tuple_types():
    df, meta = load_csv(FIXTURE)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(meta, SeriesMetadata)


def test_datetime_index():
    df, _ = load_csv(FIXTURE)
    assert isinstance(df.index, pd.DatetimeIndex)


def test_numeric_columns_detected():
    _, meta = load_csv(FIXTURE)
    assert "value" in meta.value_cols
    assert meta.timestamp_col not in meta.value_cols


def test_no_missing_values_after_ffill():
    df, _ = load_csv(FIXTURE)
    assert df.isnull().sum().sum() == 0


def test_metadata_value_range_consistent():
    df, meta = load_csv(FIXTURE)
    assert meta.value_min <= meta.value_mean <= meta.value_max


def test_metadata_length_matches_df():
    df, meta = load_csv(FIXTURE)
    assert meta.length == len(df)


def test_frequency_non_empty():
    _, meta = load_csv(FIXTURE)
    assert meta.frequency != ""


def test_bytes_input():
    raw = FIXTURE.read_bytes()
    df, meta = load_csv(raw)
    assert len(df) > 0


def test_filelike_input():
    with FIXTURE.open("rb") as fh:
        df, meta = load_csv(fh)
    assert len(df) > 0
