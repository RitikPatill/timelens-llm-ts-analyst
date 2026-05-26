# TimeLens

TimeLens — Upload a CSV, get an LLM-powered time-series analysis report.

## Status

| Milestone | Description | State |
|---|---|---|
| M1 | Scaffold: package layout, pinned dependencies, `pyproject.toml`, smoke test | Done |
| M2 | CSV ingestion and preprocessing (`ingest.py`) | Planned |
| M3 | Anomaly detection — Z-score + IQR (`detect.py`) | Planned |
| M4 | Plotly chart generation (`visualize.py`) | Planned |
| M5 | Claude LLM narrative report (`report.py`) | Planned |
| M6 | FastAPI endpoint — `POST /analyze` (`api.py`) | Planned |
| M7 | Demo GIF, polish, deployment notes | Planned |

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

Planned five-stage pipeline from raw CSV to JSON response. Module stubs are in place; implementation begins at M2.

```
CSV Upload → ingest.py → detect.py → visualize.py → report.py → JSON response
```

| Stage | Module | Responsibility |
|---|---|---|
| Ingest | `ingest.py` | Parse CSV, detect timestamp column, resample, fill gaps |
| Detect | `detect.py` | Z-score + IQR anomaly flagging |
| Visualize | `visualize.py` | Plotly chart with red anomaly markers |
| Report | `report.py` | Claude LLM narrative: trend, anomalies, next steps |
| Serve | `api.py` | `POST /analyze` → `{chart_html, report}` |

## Quickstart

> The API server requires M2–M6 to be complete. The steps below install all dependencies and verify the package is importable. The `uvicorn` command will be functional after M6.

```bash
git clone <repo-url>
cd timelens-llm-ts-analyst
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
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
│   └── test_import.py      # Smoke test: package importable, version correct
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
