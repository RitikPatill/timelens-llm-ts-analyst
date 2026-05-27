from pathlib import Path
import pytest
from timelens.ingest import load_csv
from timelens.detect import detect_anomalies
from timelens.visualize import render_chart

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


def test_render_chart_returns_nonempty_html():
    df, meta = load_csv(FIXTURE)
    df = detect_anomalies(df)
    html = render_chart(df, meta.value_cols[0])
    assert isinstance(html, str)
    assert len(html) > 0
    assert "<div" in html


def test_render_chart_without_anomaly_columns():
    """Works on a raw df (pre-detect) — anomaly overlay is simply skipped."""
    df, meta = load_csv(FIXTURE)
    html = render_chart(df, meta.value_cols[0])
    assert "<div" in html


def test_render_chart_custom_title():
    df, meta = load_csv(FIXTURE)
    html = render_chart(df, meta.value_cols[0], title="Server Latency")
    assert "Server Latency" in html
