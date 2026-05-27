"""Plotly chart generation with anomaly markers."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


def render_chart(
    df: pd.DataFrame,
    value_col: str,
    *,
    title: str = "Time Series Analysis",
) -> str:
    """Return a self-contained Plotly HTML snippet.

    Args:
        df: DataFrame with DatetimeIndex and `value_col`.  If `is_anomaly`
            (bool) and `anomaly_score` (float) columns are present they are
            used to draw the red anomaly overlay.
        value_col: name of the column to render as the main line.
        title: chart title.

    Returns:
        HTML string (<div> snippet, no surrounding <html>/<body>).
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[value_col],
            mode="lines",
            name=value_col,
        )
    )

    if "is_anomaly" in df.columns and df["is_anomaly"].any():
        anomalies = df[df["is_anomaly"]]
        scores = anomalies["anomaly_score"].values if "anomaly_score" in df.columns else [0.0] * len(anomalies)
        fig.add_trace(
            go.Scatter(
                x=anomalies.index,
                y=anomalies[value_col],
                mode="markers",
                name="Anomaly",
                marker=dict(color="red", size=10, symbol="circle-open"),
                customdata=scores,
                hovertemplate="<b>%{x}</b><br>Value: %{y}<br>Score: %{customdata:.2f}<extra></extra>",
            )
        )

    fig.update_layout(title=title)

    return pio.to_html(fig, full_html=False, include_plotlyjs=True)
