"""Tests for src/timelens/report.py — all run in offline mode."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Ensure offline mode for all tests in this module
os.environ["TIMELENS_OFFLINE"] = "1"

from timelens.detect import detect_anomalies
from timelens.ingest import load_csv
from timelens.report import (
    OFFLINE_STUB,
    ReportResult,
    _build_prompt,
    _parse_response,
    generate_report,
)

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample.csv"


@pytest.fixture(scope="module")
def sample_data():
    df, meta = load_csv(FIXTURE_CSV)
    df = detect_anomalies(df)
    return df, meta


# --- dataclass structure ---

def test_report_result_fields():
    r = ReportResult(trend_summary="t", anomaly_explanations=["a"], next_steps="n")
    assert isinstance(r.trend_summary, str)
    assert isinstance(r.anomaly_explanations, list)
    assert isinstance(r.next_steps, str)


# --- offline stub ---

def test_offline_stub_returned(monkeypatch, sample_data):
    monkeypatch.setenv("TIMELENS_OFFLINE", "1")
    df, meta = sample_data
    result = generate_report(meta, df)
    assert result is OFFLINE_STUB


def test_generate_report_returns_report_result(monkeypatch, sample_data):
    monkeypatch.setenv("TIMELENS_OFFLINE", "1")
    df, meta = sample_data
    result = generate_report(meta, df)
    assert isinstance(result, ReportResult)


# --- _build_prompt ---

def test_build_prompt_contains_metadata(sample_data):
    df, meta = sample_data
    prompt = _build_prompt(meta, df)
    assert meta.frequency in prompt
    assert str(round(meta.value_min, 4)) in prompt or f"{meta.value_min:.4g}" in prompt
    assert f"{meta.value_max:.4g}" in prompt


def test_build_prompt_contains_anomaly(sample_data):
    df, meta = sample_data
    anomalies = df[df["is_anomaly"] == True]
    if anomalies.empty:
        pytest.skip("No anomalies in sample data")
    top_ts = anomalies.sort_values("anomaly_score", ascending=False).index[0]
    prompt = _build_prompt(meta, df)
    assert str(top_ts) in prompt


# --- _parse_response ---

def test_parse_response_valid_json():
    payload = '{"trend_summary": "rising", "anomaly_explanations": ["spike at 5pm"], "next_steps": "investigate"}'
    result = _parse_response(payload)
    assert result.trend_summary == "rising"
    assert result.anomaly_explanations == ["spike at 5pm"]
    assert result.next_steps == "investigate"


def test_parse_response_malformed_json():
    result = _parse_response("this is not json at all }{")
    assert isinstance(result, ReportResult)
    assert result.trend_summary == "this is not json at all }{"
    assert result.anomaly_explanations == []
    assert result.next_steps == ""


def test_parse_response_strips_markdown_fences():
    payload = '```json\n{"trend_summary": "flat", "anomaly_explanations": [], "next_steps": "none"}\n```'
    result = _parse_response(payload)
    assert result.trend_summary == "flat"
    assert result.anomaly_explanations == []
    assert result.next_steps == "none"
