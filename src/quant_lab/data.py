from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import Bar


def load_ohlcv(path: str | Path) -> list[Bar]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"date", "open", "high", "low", "close", "volume"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"OHLCV CSV must contain {sorted(required)}")
    bars = [
        Bar(date.fromisoformat(r["date"]), *(float(r[k]) for k in ("open", "high", "low", "close", "volume")))
        for r in rows
    ]
    if any(a.date >= b.date for a, b in zip(bars, bars[1:])):
        raise ValueError("OHLCV dates must be strictly increasing")
    if any(min(b.open, b.high, b.low, b.close) <= 0 for b in bars):
        raise ValueError("Prices must be positive")
    return bars

