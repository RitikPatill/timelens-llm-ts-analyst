"""Tests for the FastAPI layer (M6)."""
import io
import os

# Must be set before importing app so generate_report returns the offline stub
os.environ["TIMELENS_OFFLINE"] = "1"

import textwrap

import pytest
from fastapi.testclient import TestClient

from timelens.api import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixture CSV helpers
# ---------------------------------------------------------------------------

def _make_csv(n_normal: int = 24, anomaly_value: float = 500.0) -> bytes:
    """25-row CSV: n_normal rows near 10.0 then one extreme anomaly."""
    lines = ["timestamp,value"]
    from datetime import datetime, timedelta
    base = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(n_normal):
        ts = base + timedelta(hours=i)
        lines.append(f"{ts.isoformat()},{10.0 + (i % 3) * 0.1:.1f}")
    anomaly_ts = base + timedelta(hours=n_normal)
    lines.append(f"{anomaly_ts.isoformat()},{anomaly_value}")
    return "\n".join(lines).encode()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_index_returns_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "TimeLens" in resp.text


def test_analyze_success():
    csv_bytes = _make_csv()
    resp = client.post(
        "/analyze",
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body.get("chart_html"), str) and body["chart_html"]
    report = body.get("report", {})
    assert "trend_summary" in report
    assert "anomaly_explanations" in report
    assert "next_steps" in report


def test_analyze_custom_threshold():
    csv_bytes = _make_csv()
    resp = client.post(
        "/analyze?threshold=1.0",
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "chart_html" in body
    assert "report" in body


def test_analyze_no_numeric_cols():
    csv_bytes = b"timestamp,label\n2024-01-01,foo\n2024-01-02,bar\n2024-01-03,baz"
    resp = client.post(
        "/analyze",
        files={"file": ("bad.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 400


def test_analyze_no_timestamp_col():
    csv_bytes = b"a,b\n1,2\n3,4\n5,6"
    resp = client.post(
        "/analyze",
        files={"file": ("notimestamp.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert resp.status_code == 400
