from __future__ import annotations

import math


def returns(values: list[float]) -> list[float]:
    return [b / a - 1.0 for a, b in zip(values, values[1:]) if a != 0]


def sharpe_ratio(values: list[float], annualization_days: int = 252) -> float:
    rs = returns(values)
    if len(rs) < 2:
        return 0.0
    mean = sum(rs) / len(rs)
    variance = sum((r - mean) ** 2 for r in rs) / (len(rs) - 1)
    return 0.0 if variance == 0 else mean / math.sqrt(variance) * math.sqrt(annualization_days)


def cagr(values: list[float], periods_per_year: int = 252) -> float:
    periods = len(values) - 1
    if periods <= 0 or values[0] <= 0 or values[-1] <= 0:
        return 0.0
    return (values[-1] / values[0]) ** (periods_per_year / periods) - 1.0


def max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1.0)
    return worst

