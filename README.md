# TimeLens – LLM Time-Series Analyst

Drop a CSV time series; get anomaly detection, trend analysis, and LLM-generated plain-English explanations in seconds.

## Status

| Milestone | Description | State |
|---|---|---|
| M1 | Scaffold: package layout, pinned dependencies, `pyproject.toml`, smoke test | Done |
| M2 | CSV ingestion and preprocessing (`ingest.py`) | Done |
| M3 | Anomaly detection — Z-score + IQR (`detect.py`) | Done |
| M4 | Plotly chart generation (`visualize.py`) | Done |
| M5 | Claude LLM narrative report (`report.py`) | Done |
| M6 | FastAPI endpoint — `POST /analyze` + HTML frontend (`api.py`, `run.py`) | Done |
| M7 | Demo GIF, polish, deployment notes | Planned |

## What works

**M6 — FastAPI backend + HTML frontend (`timelens.api`, `run.py`)**

`python run.py` → server at `http://localhost:8000`.

- `GET /` — serves a single-file dark-mode HTML page with drag-and-drop upload, Z-score threshold input, loading spinner, and inline results panel. No external resources, no build step.
- `POST /analyze?threshold=<float>` — accepts multipart CSV + optional threshold (default 2.5, range 0.1–10.0); runs the full `load_csv → detect_anomalies → render_chart → generate_report` pipeline; returns `{"chart_html": "...", "report": {"trend_summary": "...", "anomaly_explanations": [...], "next_steps": "..."}}`.
- Chart HTML injected via a `setHTML` helper that re-executes embedded `<script>` tags so the Plotly figure renders correctly.
- Report text fields set via `textContent` (not `innerHTML`) to prevent XSS from LLM output.
- Returns `HTTP 400` with a descriptive message for malformed CSVs (no timestamp column, no numeric columns).
- 5 tests pass: index HTML, success, custom threshold, no-numeric-cols 400, no-timestamp 400.

**M1 — package scaffold**
Package is installable (`pip install -e .`), version is importable, smoke test passes.

**M3 — Anomaly detection (`timelens.detect`)**

`detect_anomalies(df, *, zscore_threshold=2.5) → pd.DataFrame`

- Accepts any DataFrame with a `DatetimeIndex` and one or more numeric columns (output of `load_csv()`).
- Flags rows using Z-score method (configurable threshold, default 2.5) and IQR method (1.5×IQR bounds) independently per column.
- Guards against division-by-zero on flat series (`std=0`) and false positives on near-flat series (`IQR=0`).
- Appends `is_anomaly` (bool, union of both methods across all value columns) and `anomaly_score` (float, max absolute Z-score across columns).
- Does not mutate the input DataFrame.
- 8 tests pass covering flat series, single spike, step-change outlier, all-anomaly series, threshold sensitivity, output schema (columns and dtypes), and input immutability.

**M5 — Claude LLM narrative report (`timelens.report`)**

`generate_report(metadata, df, *, top_n=5, context_window=3) → ReportResult`

- Builds a structured prompt from `SeriesMetadata` + top-N anomaly rows with surrounding context windows.
- Calls `claude-opus-4-6` via the Anthropic streaming API; accumulates the full response via `stream.get_final_text()`.
- Parses the JSON response into a `ReportResult` dataclass with `trend_summary` (str), `anomaly_explanations` (list[str]), and `next_steps` (str).
- Strips accidental markdown fences (` ```json ``` `) from the response before parsing.
- Returns `OFFLINE_STUB` (prefixed `[offline]`) when `TIMELENS_OFFLINE=1` is set or `ANTHROPIC_API_KEY` is absent — no network call.
- Catches `anthropic.APIError` and generic exceptions; returns a `ReportResult` with the error message instead of raising.
- 7 tests pass (1 skipped when sample data contains no anomalies).

**M4 — Plotly chart generation (`timelens.visualize`)**

`render_chart(df, value_col, *, title="Time Series Analysis") → str`

- Accepts a DataFrame with DatetimeIndex — either the raw output of `load_csv()` or the enriched output of `detect_anomalies()`.
- Renders an interactive Plotly line chart for the specified value column.
- When `is_anomaly` (bool) and `anomaly_score` (float) columns are present, overlays anomaly points as red open-circle markers; hover labels show timestamp, value, and score rounded to two decimal places.
- When anomaly columns are absent the overlay is silently skipped, so the function is safe to call before running detection.
- Returns a self-contained `<div>` snippet via `plotly.io.to_html(full_html=False, include_plotlyjs=True)`; no surrounding `<html>` or `<body>` tags.
- Does not mutate the input DataFrame.
- 3 tests pass: smoke test against the bundled fixture with anomaly overlay, raw DataFrame (pre-detect) path, and custom title propagation.

**M2 — CSV ingestion and preprocessing (`timelens.ingest`)**

`load_csv(source, *, max_gap_fill=5) → tuple[pd.DataFrame, SeriesMetadata]`

- Accepts a file path, `pathlib.Path`, file-like object, or raw bytes.
- Auto-detects the timestamp column by attempting `pd.to_datetime()` on each non-numeric column; requires >80% parseable values.
- Auto-detects all numeric value columns; raises `ValueError` if none exist.
- Infers the dominant sampling frequency via `pd.infer_freq()`; falls back to median inter-sample timedelta.
- Resamples to a uniform `DatetimeIndex` and forward-fills gaps up to `max_gap_fill` consecutive rows (default 5).
- Returns a `SeriesMetadata` dataclass exposing: `timestamp_col`, `value_cols`, `length`, `frequency`, `value_min`, `value_max`, `value_mean`.
- 9 tests pass against a bundled hourly-temperature fixture (`tests/fixtures/sample.csv`).

## Why TimeLens

Ops teams and data analysts routinely wrestle with time-series CSVs—server metrics, IoT sensor readings, sales figures—yet turning raw spikes and dips into actionable prose requires either deep domain expertise or expensive BI tooling. TimeLens fills the gap: upload your CSV, get a structured report explaining what happened, where anomalies occurred, and what to investigate next.

## Demo

[GIF coming in M7]

## Stack

- Python 3.11+
- FastAPI — HTTP API and static file serving
- Pandas — CSV ingestion and preprocessing
- NumPy — numerical operations underlying anomaly detection
- Plotly — interactive chart generation
- Anthropic Claude (`claude-opus-4-6`) — LLM narrative report

## Architecture

Five-stage pipeline from raw CSV to JSON response.

```
CSV Upload → ingest.py → detect.py → visualize.py → report.py → JSON response
```

| Stage | Module | Status | Responsibility |
|---|---|---|---|
| Ingest | `ingest.py` | Done (M2) | Parse CSV, detect timestamp and numeric columns, resample to uniform frequency, forward-fill gaps, return `SeriesMetadata` |
| Detect | `detect.py` | Done (M3) | Z-score + IQR anomaly flagging |
| Visualize | `visualize.py` | Done (M4) | Plotly chart with anomaly markers |
| Report | `report.py` | Done (M5) | Claude LLM narrative: trend, anomalies, next steps |
| Serve | `api.py` | Done (M6) | `GET /` HTML UI + `POST /analyze` → `{chart_html, report}` |

## Quickstart

```bash
git clone <repo-url>
cd timelens-llm-ts-analyst
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# run all tests (offline — no Anthropic API key required):
TIMELENS_OFFLINE=1 pytest tests/

# start the server (http://localhost:8000):
python run.py
```

Open `http://localhost:8000` in your browser, drag-and-drop a CSV, and click **Analyze**.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude access |

## Project Layout

```
timelens-llm-ts-analyst/
├── src/
│   └── timelens/
│       ├── __init__.py     # Package root, exports __version__
│       ├── ingest.py       # CSV ingestion and preprocessing pipeline
│       ├── detect.py       # Anomaly detection (Z-score + IQR)
│       ├── visualize.py    # Plotly chart generation
│       ├── report.py       # Claude LLM narrative report builder
│       └── api.py          # FastAPI application entry-point
├── tests/
│   ├── __init__.py
│   ├── test_import.py          # Smoke test: package importable, version correct
│   ├── test_ingest.py          # M2 ingest pipeline tests (9 tests)
│   ├── test_detect.py          # M3 anomaly detection tests (8 tests)
│   ├── test_visualize.py       # M4 chart generation tests (3 tests)
│   ├── test_report.py          # M5 LLM report tests (8 tests, 1 conditionally skipped)
│   ├── test_api.py             # M6 FastAPI endpoint tests (5 tests)
│   └── fixtures/
│       └── sample.csv          # Hourly temperature fixture with one gap row
├── run.py              # `python run.py` starts uvicorn on :8000
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

## Roadmap

Near-term work follows the milestone table above. Post-M7 directions under consideration:

<!-- TODO: list post-launch roadmap items (e.g., multi-column series, streaming LLM response, Docker image) -->

## License

MIT — see [LICENSE](LICENSE).
