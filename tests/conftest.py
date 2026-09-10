from datetime import date, timedelta

from quant_lab.models import Bar, Hypothesis


def bars(closes, opens=None):
    opens = opens or closes
    start = date(2025, 1, 1)
    return [Bar(start + timedelta(days=i), o, max(o, c), min(o, c), c, 1_000_000) for i, (o, c) in enumerate(zip(opens, closes))]


def hypothesis(**kwargs):
    defaults = dict(id="H1", name="test", strategy="sma_cross", symbol="X", parameters={"fast": 1, "slow": 2}, initial_cash=1000, fees_bps=0, slippage_bps=0, annualization_days=252)
    defaults.update(kwargs)
    return Hypothesis(**defaults)

