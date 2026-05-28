"""Claude LLM narrative report builder."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import pandas as pd

from timelens.ingest import SeriesMetadata

_MODEL = "claude-opus-4-6"

OFFLINE_STUB = None  # set after dataclass definition


@dataclass
class ReportResult:
    trend_summary: str
    anomaly_explanations: list[str] = field(default_factory=list)
    next_steps: str = ""


OFFLINE_STUB = ReportResult(
    trend_summary="[offline] Trend summary not available in offline mode.",
    anomaly_explanations=["[offline] Anomaly explanations not available in offline mode."],
    next_steps="[offline] Next steps not available in offline mode.",
)


def _build_prompt(
    metadata: SeriesMetadata,
    df: pd.DataFrame,
    top_n: int = 5,
    context_window: int = 3,
) -> str:
    """Build a structured prompt from metadata and anomaly rows. Pure function."""
    meta_section = (
        f"## Time Series Metadata\n"
        f"- Length: {metadata.length} rows\n"
        f"- Frequency: {metadata.frequency}\n"
        f"- Value columns: {', '.join(metadata.value_cols)}\n"
        f"- Value range: [{metadata.value_min:.4g}, {metadata.value_max:.4g}]\n"
        f"- Value mean: {metadata.value_mean:.4g}\n"
    )

    anomaly_section = ""
    if "is_anomaly" in df.columns and "anomaly_score" in df.columns:
        anomalies = (
            df[df["is_anomaly"] == True]
            .sort_values("anomaly_score", ascending=False)
            .head(top_n)
        )
        if not anomalies.empty:
            anomaly_section = "\n## Top Anomalies with Context\n"
            for rank, (ts, row) in enumerate(anomalies.iterrows(), start=1):
                pos = df.index.get_loc(ts)
                start = max(0, pos - context_window)
                end = min(len(df), pos + context_window + 1)
                window = df.iloc[start:end]

                anomaly_section += f"\n### Anomaly {rank} — {ts} (score={row['anomaly_score']:.4g})\n"
                anomaly_section += "| timestamp | " + " | ".join(metadata.value_cols) + " | anomaly_score |\n"
                anomaly_section += "|---|" + "---|" * len(metadata.value_cols) + "---|\n"
                for t, r in window.iterrows():
                    vals = " | ".join(f"{r[c]:.4g}" if c in r.index else "N/A" for c in metadata.value_cols)
                    score = f"{r['anomaly_score']:.4g}" if "anomaly_score" in r.index else "N/A"
                    marker = " **<-- anomaly**" if t == ts else ""
                    anomaly_section += f"| {t} | {vals} | {score} |{marker}\n"

    json_instruction = (
        "\n## Output Instructions\n"
        "Respond with ONLY valid JSON (no markdown fences, no prose) in this exact schema:\n"
        '{\n'
        '  "trend_summary": "...",\n'
        '  "anomaly_explanations": ["...", "..."],\n'
        '  "next_steps": "..."\n'
        '}\n'
    )

    return meta_section + anomaly_section + json_instruction


def _parse_response(text: str) -> ReportResult:
    """Parse Claude's JSON response into a ReportResult. Never raises."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        data = json.loads(cleaned)
        return ReportResult(
            trend_summary=data.get("trend_summary", ""),
            anomaly_explanations=data.get("anomaly_explanations", []),
            next_steps=data.get("next_steps", ""),
        )
    except Exception:
        return ReportResult(
            trend_summary=text,
            anomaly_explanations=[],
            next_steps="",
        )


def generate_report(
    metadata: SeriesMetadata,
    df: pd.DataFrame,
    top_n: int = 5,
    context_window: int = 3,
) -> ReportResult:
    """Generate an LLM narrative report for the time series.

    Returns OFFLINE_STUB when TIMELENS_OFFLINE=1 or ANTHROPIC_API_KEY is absent.
    """
    if os.environ.get("TIMELENS_OFFLINE") or not os.environ.get("ANTHROPIC_API_KEY"):
        return OFFLINE_STUB

    if "is_anomaly" not in df.columns:
        return OFFLINE_STUB

    prompt = _build_prompt(metadata, df, top_n=top_n, context_window=context_window)

    try:
        import anthropic

        client = anthropic.Anthropic()
        with client.messages.stream(
            model=_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            text = stream.get_final_text()
        return _parse_response(text)
    except Exception as e:
        return ReportResult(
            trend_summary=f"API error: {e}",
            anomaly_explanations=[],
            next_steps="",
        )
