from __future__ import annotations

import math

from .backtester import run_backtest
from .models import Bar, DatasetSplit, GateRules, Hypothesis, ValidationReport
from .strategies import Strategy

STAGES = ("TRAIN", "VALIDATION", "VAULT")


def split_bars(bars: list[Bar], config: DatasetSplit = DatasetSplit()) -> dict[str, list[Bar]]:
    if not 0 < config.train_fraction < 1 or not 0 < config.validation_fraction < 1:
        raise ValueError("Split fractions must be between zero and one")
    if config.train_fraction + config.validation_fraction >= 1:
        raise ValueError("TRAIN + VALIDATION must leave a non-empty VAULT")
    if len(bars) < 6:
        raise ValueError("At least six bars are required for three validation stages")
    validation_size = max(2, int(len(bars) * config.validation_fraction))
    train_size = max(2, int(len(bars) * config.train_fraction))
    if train_size + validation_size > len(bars) - 2:
        train_size = len(bars) - validation_size - 2
    train_end = train_size
    validation_end = train_end + validation_size
    parts = {
        "TRAIN": bars[:train_end],
        "VALIDATION": bars[train_end:validation_end],
        "VAULT": bars[validation_end:],
    }
    if any(len(part) < 2 for part in parts.values()):
        raise ValueError("Each dataset split requires at least two bars")
    return parts


def gate(metrics: dict[str, float], rules: GateRules) -> str | None:
    checks = (
        (metrics["trade_count"] < rules.min_trades, "insufficient trades"),
        (metrics["sharpe"] < rules.min_sharpe, "Sharpe below threshold"),
        (abs(metrics["max_drawdown"]) > rules.max_drawdown, "drawdown above threshold"),
        (metrics["profit_factor"] < rules.min_profit_factor, "profit factor below threshold"),
        (rules.must_be_profitable and metrics["total_return"] <= 0, "strategy is not profitable"),
    )
    return next((reason for failed, reason in checks if failed), None)


def score_report(stages: dict[str, dict[str, float]]) -> float:
    if "VALIDATION" not in stages:
        return 0.0
    validation = stages["VALIDATION"]
    vault = stages.get("VAULT", validation)
    sharpe = max(0.0, min(1.0, (validation["sharpe"] + vault["sharpe"]) / 4.0))
    drawdown = max(0.0, 1.0 - abs(max(validation["max_drawdown"], vault["max_drawdown"], key=abs)) / 0.30)
    profitability = 1.0 if validation["total_return"] > 0 and vault["total_return"] > 0 else 0.0
    degradation = 1.0
    train_sharpe = stages["TRAIN"]["sharpe"]
    if train_sharpe > 0:
        degradation = max(0.0, min(1.0, validation["sharpe"] / train_sharpe))
    value = 35 * sharpe + 25 * drawdown + 20 * profitability + 20 * degradation
    return round(value, 2) if math.isfinite(value) else 0.0


def validate_strategy(
    hypothesis: Hypothesis,
    bars: list[Bar],
    strategy: Strategy,
    rules: dict[str, GateRules] | None = None,
    split: DatasetSplit = DatasetSplit(),
) -> ValidationReport:
    rules = rules or {
        "TRAIN": GateRules(),
        "VALIDATION": GateRules(min_sharpe=0.7, max_drawdown=0.25, min_profit_factor=1.05),
        "VAULT": GateRules(min_sharpe=0.5, max_drawdown=0.25, min_profit_factor=1.0),
    }
    results: dict[str, dict[str, float]] = {}
    for stage, stage_bars in split_bars(bars, split).items():
        result = run_backtest(hypothesis, stage_bars, strategy)
        results[stage] = result.metrics
        rejection = gate(result.metrics, rules[stage])
        if rejection:
            return ValidationReport(
                status="REJECTED",
                score=score_report(results),
                stages=results,
                rejection_reason=f"{stage}: {rejection}",
            )
    return ValidationReport(status="VAULT_PASS", score=score_report(results), stages=results)
