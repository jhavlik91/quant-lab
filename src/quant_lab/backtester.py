from __future__ import annotations

from .metrics import cagr, max_drawdown, sharpe_ratio
from .models import BacktestResult, Bar, EquityPoint, Hypothesis, Trade
from .strategies import Strategy

ENGINE_VERSION = "0.2.0"


def run_backtest(h: Hypothesis, bars: list[Bar], strategy: Strategy) -> BacktestResult:
    if len(bars) < 2:
        raise ValueError("At least two bars are required")
    targets = strategy.target_weights(bars)
    if len(targets) != len(bars) or any(t not in (0.0, 1.0) for t in targets):
        raise ValueError("MVP strategies must emit one binary long-only target per bar")

    cash, qty = h.initial_cash, 0.0
    entry_date = None
    entry_price = entry_fees = entry_slippage = 0.0
    trades: list[Trade] = []
    benchmark_qty = h.initial_cash / bars[0].open
    curve = [EquityPoint(bars[0].date, cash, h.initial_cash)]

    # target[i-1] is derived from close[i-1], then executed at open[i].
    for i in range(1, len(bars)):
        target, bar = targets[i - 1], bars[i]
        fee_rate, slip_rate = h.fees_bps / 10_000, h.slippage_bps / 10_000
        if target == 1.0 and qty == 0.0:
            fill = bar.open * (1 + slip_rate)
            qty = cash / (fill * (1 + fee_rate))
            notional = qty * fill
            entry_fees, entry_slippage = notional * fee_rate, qty * (fill - bar.open)
            cash, entry_date, entry_price = 0.0, bar.date, fill
        elif target == 0.0 and qty > 0.0:
            fill = bar.open * (1 - slip_rate)
            notional = qty * fill
            exit_fee = notional * fee_rate
            exit_slippage = qty * (bar.open - fill)
            cash = notional - exit_fee
            trades.append(Trade(entry_date, entry_price, bar.date, fill, qty, entry_fees + exit_fee,
                                entry_slippage + exit_slippage,
                                cash - qty * entry_price - entry_fees))
            qty = 0.0
        equity = cash + qty * bar.close
        curve.append(EquityPoint(bar.date, equity, benchmark_qty * bar.close))

    if qty > 0.0:
        bar = bars[-1]
        fill = bar.close * (1 - h.slippage_bps / 10_000)
        exit_fee = qty * fill * h.fees_bps / 10_000
        exit_slippage = qty * (bar.close - fill)
        cash = qty * fill - exit_fee
        trades.append(Trade(entry_date, entry_price, bar.date, fill, qty, entry_fees + exit_fee,
                            entry_slippage + exit_slippage,
                            cash - qty * entry_price - entry_fees))
        curve[-1] = EquityPoint(bar.date, cash, curve[-1].benchmark_equity)

    equity = [p.equity for p in curve]
    benchmark = [p.benchmark_equity for p in curve]
    total_fees = sum(t.fees for t in trades)
    total_slippage = sum(t.slippage for t in trades)
    winners = [t for t in trades if t.pnl > 0]
    gross_profit = sum(t.pnl for t in winners)
    gross_loss = -sum(t.pnl for t in trades if t.pnl < 0)
    metrics = {
        "total_return": equity[-1] / equity[0] - 1,
        "cagr": cagr(equity, h.annualization_days),
        "sharpe": sharpe_ratio(equity, h.annualization_days),
        "max_drawdown": max_drawdown(equity),
        "benchmark_return": benchmark[-1] / benchmark[0] - 1,
        "excess_return": equity[-1] / equity[0] - benchmark[-1] / benchmark[0],
        "trade_count": float(len(trades)),
        "profit_factor": gross_profit / gross_loss if gross_loss else (1_000_000.0 if gross_profit else 0.0),
        "win_rate": len(winners) / len(trades) if trades else 0.0,
        "avg_trade": sum(t.pnl for t in trades) / len(trades) if trades else 0.0,
        "fees": total_fees,
        "slippage": total_slippage,
    }
    return BacktestResult(metrics, trades, curve)
