# TimeLens – LLM Time-Series Analyst

Drop a CSV time series; get anomaly detection, trend analysis, and LLM-generated plain-English explanations in seconds.

## Status

| Milestone | Description | State |
|---|---|---|
| M1 | Scaffold: package layout, pinned dependencies, `pyproject.toml`, smoke test | Done |
| M2 | CSV ingestion and preprocessing (`ingest.py`) | Done |
| M3 | Anomaly detection — Z-score + IQR (`detect.py`) | Planned |
| M4 | Plotly chart generation (`visualize.py`) | Planned |
| M5 | Claude LLM narrative report (`report.py`) | Planned |
| M6 | FastAPI endpoint — `POST /analyze` (`api.py`) | Planned |
| M7 | Demo GIF, polish, deployment notes | Planned |

## What works

**M1 — package scaffold**
Package is installable (`pip install -e .`), version is importable, smoke test passes.

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
- Anthropic Claude (`claude-sonnet-4-6`) — LLM narrative report

## Architecture

Five-stage pipeline from raw CSV to JSON response.

```
CSV Upload → ingest.py → detect.py → visualize.py → report.py → JSON response
```

| Stage | Module | Status | Responsibility |
|---|---|---|---|
| Ingest | `ingest.py` | Done (M2) | Parse CSV, detect timestamp and numeric columns, resample to uniform frequency, forward-fill gaps, return `SeriesMetadata` |
| Detect | `detect.py` | Stub (M3) | Z-score + IQR anomaly flagging |
| Visualize | `visualize.py` | Stub (M4) | Plotly chart with anomaly markers |
| Report | `report.py` | Stub (M5) | Claude LLM narrative: trend, anomalies, next steps |
| Serve | `api.py` | Stub (M6) | `POST /analyze` → `{chart_html, report}` |

## Quickstart

> The API server requires M2–M6 to be complete. The steps below install all dependencies and verify the package is importable. The `uvicorn` command will be functional after M6.

```bash
git clone <repo-url>
cd timelens-llm-ts-analyst
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# verify the ingestion pipeline (M2 — all 9 tests pass):
pytest tests/

# available after M6:
# uvicorn timelens.api:app --reload
```

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
│   └── fixtures/
│       └── sample.csv          # Hourly temperature fixture with one gap row
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
