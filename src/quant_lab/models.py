from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Bar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Hypothesis:
    id: str
    name: str
    strategy: str
    symbol: str
    parameters: dict[str, Any]
    initial_cash: float = 100_000.0
    fees_bps: float = 5.0
    slippage_bps: float = 10.0
    annualization_days: int = 252


@dataclass(frozen=True)
class Trade:
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    quantity: float
    fees: float
    slippage: float
    pnl: float


@dataclass(frozen=True)
class EquityPoint:
    date: date
    equity: float
    benchmark_equity: float


@dataclass
class BacktestResult:
    metrics: dict[str, float]
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)


@dataclass(frozen=True)
class GateRules:
    min_trades: int = 20
    min_sharpe: float = 0.8
    max_drawdown: float = 0.30
    min_profit_factor: float = 1.10
    must_be_profitable: bool = True


@dataclass(frozen=True)
class DatasetSplit:
    train_fraction: float = 0.60
    validation_fraction: float = 0.20


@dataclass
class ValidationReport:
    status: str
    score: float
    stages: dict[str, dict[str, float]]
    rejection_reason: str | None = None
