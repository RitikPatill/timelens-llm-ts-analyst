"""Anomaly detection engine — Z-score and IQR methods."""

import pandas as pd
import numpy as np


def detect_anomalies(
    df: pd.DataFrame,
    *,
    zscore_threshold: float = 2.5,
) -> pd.DataFrame:
    """Return df augmented with is_anomaly (bool) and anomaly_score (float).

    Both Z-score and IQR methods are applied per numeric column; a row is
    flagged when either method triggers on any column.  anomaly_score is the
    max absolute Z-score across all value columns for that row.

    The input DataFrame is not mutated.
    """
    df = df.copy()

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    zscore_flags = pd.DataFrame(False, index=df.index, columns=numeric_cols)
    iqr_flags = pd.DataFrame(False, index=df.index, columns=numeric_cols)
    zscore_abs = pd.DataFrame(0.0, index=df.index, columns=numeric_cols)

    for col in numeric_cols:
        series = df[col]

        # Z-score method
        std = series.std(ddof=0)
        if std == 0:
            z = pd.Series(0.0, index=series.index)
        else:
            z = (series - series.mean()) / std
        zscore_abs[col] = z.abs()
        zscore_flags[col] = z.abs() > zscore_threshold

        # IQR method
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr != 0:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            iqr_flags[col] = (series < lower) | (series > upper)

    df["is_anomaly"] = zscore_flags.any(axis=1) | iqr_flags.any(axis=1)
    df["anomaly_score"] = zscore_abs.max(axis=1)

    return df
