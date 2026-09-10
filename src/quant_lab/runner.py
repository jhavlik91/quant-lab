from __future__ import annotations

import json
import os
from pathlib import Path

from .backtester import run_backtest
from .data import load_ohlcv
from .models import Hypothesis
from .registry import ExperimentRegistry
from .strategies import strategy_from


def run_one(hypothesis_path: Path, data_path: Path, database_path: Path) -> dict[str, object]:
    payload = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis = Hypothesis(**payload)
    result = run_backtest(
        hypothesis,
        load_ohlcv(data_path),
        strategy_from(hypothesis.strategy, hypothesis.parameters),
    )
    experiment_id = ExperimentRegistry(database_path).save(hypothesis, data_path.read_bytes(), result)
    return {"experiment_id": experiment_id, "mode": "PAPER", "metrics": result.metrics}


def run_job(job_path: Path) -> dict[str, object]:
    config = json.loads(job_path.read_text(encoding="utf-8"))
    if config.get("mode") != "PAPER":
        raise ValueError("Only mode=PAPER is supported")
    base = job_path.resolve().parent
    database = Path(os.environ.get("QUANT_LAB_DB", base / config.get("database", "quant_lab.db")))
    runs = config.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("Job requires a non-empty runs list")
    results = []
    for item in runs:
        results.append(run_one(base / item["hypothesis"], base / item["ohlcv"], database))
    return {"mode": "PAPER", "database": str(database), "completed": len(results), "runs": results}
