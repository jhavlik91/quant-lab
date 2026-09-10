import unittest

from quant_lab.backtester import run_backtest
from quant_lab.strategies import SmaCrossStrategy

from conftest import bars, hypothesis


class CostTests(unittest.TestCase):
    def test_fees_and_slippage_reduce_result(self):
        data = bars([10, 11, 12, 13, 14])
        free = run_backtest(hypothesis(), data, SmaCrossStrategy(1, 2))
        costly = run_backtest(hypothesis(fees_bps=10, slippage_bps=20), data, SmaCrossStrategy(1, 2))
        self.assertLess(costly.metrics["total_return"], free.metrics["total_return"])
        self.assertGreater(costly.metrics["fees"], 0)
        self.assertGreater(costly.metrics["slippage"], 0)
