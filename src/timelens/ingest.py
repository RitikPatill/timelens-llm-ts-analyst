"""CSV ingestion and preprocessing pipeline."""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd


@dataclass
class SeriesMetadata:
    timestamp_col: str
    value_cols: list[str]
    length: int
    frequency: str      # pandas offset alias, e.g. "1h", "1min"
    value_min: float
    value_max: float
    value_mean: float


def _detect_timestamp_col(df: pd.DataFrame) -> str:
    """Return the column name most likely to contain datetimes.

    Tries pd.to_datetime() on each column; picks the one with the
    highest fraction of successfully parsed values.
    Raises ValueError if no candidate is found.
    """
    numeric_cols = set(df.select_dtypes(include="number").columns.tolist())
    best_col = None
    best_ratio = 0.0

    for col in df.columns:
        if col in numeric_cols:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        ratio = parsed.notna().mean()
        if ratio > best_ratio:
            best_ratio = ratio
            best_col = col

    if best_col is None or best_ratio < 0.8:
        raise ValueError("No timestamp column detected (need >80% parseable values).")
    return best_col


def _infer_frequency(index: pd.DatetimeIndex) -> str:
    """Return a pandas offset alias for the dominant interval.

    Tries pd.infer_freq() first; falls back to median timedelta
    converted to a pandas Timedelta offset string.
    """
    freq = pd.infer_freq(index)
    if freq is not None:
        return freq

    deltas = np.diff(index.asi8)
    median_ns = float(np.median(deltas))
    offset = pd.tseries.frequencies.to_offset(pd.Timedelta(median_ns))
    if offset is None:
        raise ValueError("Unable to infer frequency from the time series index.")
    return offset.freqstr


def load_csv(
    source: Union[str, Path, io.IOBase, bytes],
    *,
    max_gap_fill: int = 5,
) -> tuple[pd.DataFrame, SeriesMetadata]:
    """Load, clean and resample a time-series CSV.

    Args:
        source: file path, Path, file-like object, or raw bytes.
        max_gap_fill: maximum consecutive NaNs to forward-fill after
                      resampling.

    Returns:
        (df, meta) where df has a DatetimeIndex and only numeric columns,
        and meta is a populated SeriesMetadata.

    Raises:
        ValueError: if no timestamp column or no numeric columns are found.
    """
    if isinstance(source, bytes):
        source = io.BytesIO(source)

    df = pd.read_csv(source)

    ts_col = _detect_timestamp_col(df)
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    df = df.set_index(ts_col).sort_index()

    value_cols = df.select_dtypes(include="number").columns.tolist()
    if not value_cols:
        raise ValueError("No numeric columns found in CSV.")
    df = df[value_cols]

    freq = _infer_frequency(df.index)
    df = df.resample(freq, origin="start").mean()
    df = df.ffill(limit=max_gap_fill)

    meta = SeriesMetadata(
        timestamp_col=ts_col,
        value_cols=value_cols,
        length=len(df),
        frequency=freq,
        value_min=float(df[value_cols].values.min()),
        value_max=float(df[value_cols].values.max()),
        value_mean=float(df[value_cols].values.mean()),
    )
    return df, meta
