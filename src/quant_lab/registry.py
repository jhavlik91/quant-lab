from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict
from pathlib import Path

from .backtester import ENGINE_VERSION
from .models import BacktestResult, Hypothesis


class ExperimentRegistry:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
          id TEXT PRIMARY KEY, hypothesis_id TEXT NOT NULL, hypothesis_json TEXT NOT NULL,
          data_hash TEXT NOT NULL, engine_version TEXT NOT NULL, mode TEXT NOT NULL CHECK(mode='PAPER'),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS metrics (
          experiment_id TEXT NOT NULL, name TEXT NOT NULL, value REAL NOT NULL,
          PRIMARY KEY(experiment_id, name), FOREIGN KEY(experiment_id) REFERENCES experiments(id));
        CREATE TABLE IF NOT EXISTS trades (
          experiment_id TEXT NOT NULL, sequence INTEGER NOT NULL, payload TEXT NOT NULL,
          PRIMARY KEY(experiment_id, sequence), FOREIGN KEY(experiment_id) REFERENCES experiments(id));
        CREATE TABLE IF NOT EXISTS equity_curve (
          experiment_id TEXT NOT NULL, sequence INTEGER NOT NULL, payload TEXT NOT NULL,
          PRIMARY KEY(experiment_id, sequence), FOREIGN KEY(experiment_id) REFERENCES experiments(id));
        """)

    def save(self, h: Hypothesis, raw_data: bytes, result: BacktestResult) -> str:
        experiment_id = str(uuid.uuid4())
        hypothesis_json = json.dumps(asdict(h), sort_keys=True, separators=(",", ":"))
        data_hash = hashlib.sha256(raw_data).hexdigest()
        with self.connection:
            self.connection.execute(
                "INSERT INTO experiments(id,hypothesis_id,hypothesis_json,data_hash,engine_version,mode) VALUES(?,?,?,?,?,'PAPER')",
                (experiment_id, h.id, hypothesis_json, data_hash, ENGINE_VERSION),
            )
            self.connection.executemany(
                "INSERT INTO metrics VALUES(?,?,?)",
                ((experiment_id, k, v) for k, v in result.metrics.items()),
            )
            self.connection.executemany(
                "INSERT INTO trades VALUES(?,?,?)",
                ((experiment_id, i, json.dumps(asdict(t), default=str)) for i, t in enumerate(result.trades)),
            )
            self.connection.executemany(
                "INSERT INTO equity_curve VALUES(?,?,?)",
                ((experiment_id, i, json.dumps(asdict(p), default=str)) for i, p in enumerate(result.equity_curve)),
            )
        return experiment_id

    def list_experiments(self, limit: int = 20) -> list[dict[str, object]]:
        rows = self.connection.execute(
            "SELECT id,hypothesis_id,engine_version,mode,created_at FROM experiments ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        keys = ("id", "hypothesis_id", "engine_version", "mode", "created_at")
        return [dict(zip(keys, row)) for row in rows]

    def get_experiment(self, experiment_id: str) -> dict[str, object] | None:
        row = self.connection.execute(
            "SELECT id,hypothesis_id,hypothesis_json,data_hash,engine_version,mode,created_at FROM experiments WHERE id=?",
            (experiment_id,),
        ).fetchone()
        if row is None:
            return None
        keys = ("id", "hypothesis_id", "hypothesis", "data_hash", "engine_version", "mode", "created_at")
        result = dict(zip(keys, row))
        result["hypothesis"] = json.loads(str(result["hypothesis"]))
        result["metrics"] = dict(self.connection.execute(
            "SELECT name,value FROM metrics WHERE experiment_id=? ORDER BY name", (experiment_id,)
        ).fetchall())
        return result

