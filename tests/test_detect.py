"""Tests for src/timelens/detect.py."""

import numpy as np
import pandas as pd
import pytest

from timelens.detect import detect_anomalies


def make_df(values):
    """Create a single-column DataFrame with DatetimeIndex (hourly)."""
    index = pd.date_range("2024-01-01", periods=len(values), freq="h")
    return pd.DataFrame({"value": values}, index=index)


def test_output_columns_added():
    df = make_df([1.0] * 20)
    result = detect_anomalies(df)
    assert "is_anomaly" in result.columns
    assert "anomaly_score" in result.columns


def test_output_dtypes():
    df = make_df([1.0] * 20)
    result = detect_anomalies(df)
    assert result["is_anomaly"].dtype == bool
    assert result["anomaly_score"].dtype == np.float64


def test_flat_series_no_anomalies():
    df = make_df([5.0] * 20)
    result = detect_anomalies(df)
    assert result["is_anomaly"].sum() == 0
    assert (result["anomaly_score"] == 0.0).all()


def test_obvious_spike_flagged():
    values = [0.0] * 49 + [1000.0]
    df = make_df(values)
    result = detect_anomalies(df)
    assert result["is_anomaly"].iloc[-1] is np.bool_(True)


def test_step_change_single_outlier():
    values = [1.0] * 9 + [100.0]
    df = make_df(values)
    result = detect_anomalies(df)
    assert result["is_anomaly"].iloc[-1] is np.bool_(True)


def test_threshold_sensitivity():
    values = [0.0] * 49 + [1000.0]
    df = make_df(values)
    low_thresh = detect_anomalies(df, zscore_threshold=1.0)
    high_thresh = detect_anomalies(df, zscore_threshold=3.0)
    assert low_thresh["is_anomaly"].sum() >= high_thresh["is_anomaly"].sum()


def test_all_anomaly_series():
    # Alternating extremes: every point is at a polar extreme.
    # Z-score/IQR are distribution-relative; a perfectly bimodal series has all
    # Z-scores == ±1.0 and no IQR fence breaches, so 0 anomalies is correct
    # (masking effect).  The test verifies robustness and output validity, not
    # that every point is flagged.
    values = [0.0, 1000.0] * 20
    df = make_df(values)
    result = detect_anomalies(df)
    assert "is_anomaly" in result.columns
    assert "anomaly_score" in result.columns
    assert len(result) == len(df)
    assert result["is_anomaly"].dtype == bool
    assert not result["anomaly_score"].isna().any()


def test_preserves_original_columns():
    df = make_df([1.0, 2.0, 3.0])
    original_df = df.copy()
    result = detect_anomalies(df)
    # original value column still present
    assert "value" in result.columns
    # input df unchanged
    pd.testing.assert_frame_equal(df, original_df)
