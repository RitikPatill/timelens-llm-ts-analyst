"""FastAPI application — TimeLens M6 backend + HTML frontend."""
from __future__ import annotations

import dataclasses

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse

from timelens.detect import detect_anomalies
from timelens.ingest import load_csv
from timelens.report import generate_report
from timelens.visualize import render_chart

app = FastAPI(title="TimeLens")

# ---------------------------------------------------------------------------
# Single-file HTML frontend
# ---------------------------------------------------------------------------
_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>TimeLens</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0f1117;
    color: #e2e8f0;
    font-family: system-ui, -apple-system, sans-serif;
    min-height: 100vh;
    padding: 2rem 1rem;
  }
  h1 { color: #7dd3fc; font-size: 2rem; margin-bottom: 0.25rem; }
  .subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.95rem; }
  #drop-zone {
    border: 2px dashed #334155;
    border-radius: 12px;
    padding: 3rem 2rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    background: #1e293b;
    margin-bottom: 1.5rem;
  }
  #drop-zone.dragover { border-color: #7dd3fc; background: #1e3a5f; }
  #drop-zone p { color: #94a3b8; margin-bottom: 0.5rem; }
  #drop-zone .file-name { color: #7dd3fc; font-weight: 600; font-size: 1.05rem; }
  .controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }
  label { color: #94a3b8; font-size: 0.9rem; }
  input[type=number] {
    background: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
    padding: 0.4rem 0.7rem;
    border-radius: 6px;
    width: 80px;
    font-size: 0.95rem;
  }
  button {
    background: #7dd3fc;
    color: #0f1117;
    border: none;
    padding: 0.55rem 1.4rem;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.95rem;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  button:disabled { opacity: 0.35; cursor: not-allowed; }
  /* Spinner */
  #spinner {
    display: none;
    align-items: center;
    gap: 0.75rem;
    color: #7dd3fc;
    margin-bottom: 1.5rem;
  }
  .ring {
    width: 28px; height: 28px;
    border: 3px solid #1e293b;
    border-top-color: #7dd3fc;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  /* Error */
  #error {
    display: none;
    background: #3b1f2b;
    border: 1px solid #ef4444;
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    color: #fca5a5;
    margin-bottom: 1.5rem;
  }
  /* Results */
  #results { display: none; }
  #chart-container { margin-bottom: 1.5rem; }
  .report-section { margin-bottom: 1.5rem; }
  .report-section h2 {
    color: #7dd3fc;
    font-size: 1.1rem;
    margin-bottom: 0.6rem;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 0.4rem;
  }
  .report-section p, .report-section .text-block {
    color: #cbd5e1;
    line-height: 1.65;
    font-size: 0.95rem;
  }
  .anomaly-item {
    background: #1e293b;
    border-left: 3px solid #f87171;
    padding: 0.6rem 0.9rem;
    border-radius: 0 6px 6px 0;
    margin-bottom: 0.5rem;
    color: #cbd5e1;
    font-size: 0.9rem;
    line-height: 1.55;
  }
</style>
</head>
<body>
<h1>TimeLens</h1>
<p class="subtitle">Drop a CSV with time-stamped data and get an instant analysis report.</p>

<div id="drop-zone">
  <p>Drag &amp; drop a CSV file here, or click to browse</p>
  <span class="file-name" id="file-name-display"></span>
  <input type="file" id="file-input" accept=".csv" hidden/>
</div>

<div class="controls">
  <label for="threshold">Z-score threshold</label>
  <input type="number" id="threshold" value="2.5" step="0.1" min="0.1" max="10.0"/>
  <button id="upload-btn" disabled>Analyze</button>
</div>

<div id="spinner"><div class="ring"></div><span>Analyzing…</span></div>
<div id="error"></div>

<div id="results">
  <div id="chart-container"></div>
  <div class="report-section" id="trend-section">
    <h2>Trend Summary</h2>
    <p id="trend-summary" class="text-block"></p>
  </div>
  <div class="report-section" id="anomaly-section">
    <h2>Anomaly Explanations</h2>
    <div id="anomaly-list"></div>
  </div>
  <div class="report-section" id="next-section">
    <h2>Next Steps</h2>
    <p id="next-steps" class="text-block"></p>
  </div>
</div>

<script>
(function () {
  var fileInput   = document.getElementById('file-input');
  var dropZone    = document.getElementById('drop-zone');
  var fileDisplay = document.getElementById('file-name-display');
  var uploadBtn   = document.getElementById('upload-btn');
  var spinner     = document.getElementById('spinner');
  var errorDiv    = document.getElementById('error');
  var results     = document.getElementById('results');
  var selectedFile = null;

  function setFile(file) {
    selectedFile = file;
    fileDisplay.textContent = file.name;
    uploadBtn.disabled = false;
  }

  dropZone.addEventListener('click', function () { fileInput.click(); });
  fileInput.addEventListener('change', function () {
    if (fileInput.files.length) setFile(fileInput.files[0]);
  });
  dropZone.addEventListener('dragover', function (e) {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  dropZone.addEventListener('dragleave', function () {
    dropZone.classList.remove('dragover');
  });
  dropZone.addEventListener('drop', function (e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    var file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  uploadBtn.addEventListener('click', analyze);

  function setHTML(el, html) {
    el.innerHTML = html;
    el.querySelectorAll('script').forEach(function (old) {
      var s = document.createElement('script');
      Array.from(old.attributes).forEach(function (a) { s.setAttribute(a.name, a.value); });
      s.textContent = old.textContent;
      old.replaceWith(s);
    });
  }

  function renderResults(data) {
    setHTML(document.getElementById('chart-container'), data.chart_html);

    var report = data.report;
    document.getElementById('trend-summary').textContent = report.trend_summary || '';
    document.getElementById('next-steps').textContent    = report.next_steps   || '';

    var list = document.getElementById('anomaly-list');
    list.innerHTML = '';
    var explanations = report.anomaly_explanations || [];
    if (explanations.length === 0) {
      var none = document.createElement('p');
      none.className = 'text-block';
      none.textContent = 'No anomalies detected.';
      list.appendChild(none);
    } else {
      explanations.forEach(function (text) {
        var div = document.createElement('div');
        div.className = 'anomaly-item';
        div.textContent = text;
        list.appendChild(div);
      });
    }

    results.style.display = 'block';
    results.scrollIntoView({ behavior: 'smooth' });
  }

  function analyze() {
    if (!selectedFile) return;

    errorDiv.style.display = 'none';
    results.style.display  = 'none';
    spinner.style.display  = 'flex';
    uploadBtn.disabled     = true;

    var threshold = parseFloat(document.getElementById('threshold').value) || 2.5;
    var form = new FormData();
    form.append('file', selectedFile);

    fetch('/analyze?threshold=' + threshold, { method: 'POST', body: form })
      .then(function (res) {
        return res.json().then(function (body) {
          if (!res.ok) throw new Error(body.detail || 'Server error ' + res.status);
          return body;
        });
      })
      .then(function (data) {
        spinner.style.display = 'none';
        uploadBtn.disabled    = false;
        renderResults(data);
      })
      .catch(function (err) {
        spinner.style.display  = 'none';
        uploadBtn.disabled     = false;
        errorDiv.textContent   = err.message;
        errorDiv.style.display = 'block';
      });
  }
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(content=_HTML)


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    threshold: float = Query(default=2.5, ge=0.1, le=10.0),
) -> dict:
    try:
        contents = await file.read()
        df, meta = load_csv(contents)
        df = detect_anomalies(df, zscore_threshold=threshold)
        chart_html = render_chart(df, meta.value_cols[0], title=f"TimeLens: {meta.value_cols[0]}")
        report = generate_report(meta, df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "chart_html": chart_html,
        "report": dataclasses.asdict(report),
    }
