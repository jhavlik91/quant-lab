import unittest

from quant_lab.backtester import run_backtest
from quant_lab.strategies import SmaCrossStrategy

from conftest import bars, hypothesis


class LookAheadTests(unittest.TestCase):
    def test_signal_at_close_executes_only_at_next_open(self):
        data = bars([10, 20, 20, 20], opens=[10, 20, 100, 100])
        result = run_backtest(hypothesis(), data, SmaCrossStrategy(1, 2))
        self.assertEqual(result.trades[0].entry_date, data[2].date)
        self.assertEqual(result.trades[0].entry_price, 100)

    def test_future_close_does_not_change_past_entry(self):
        first = run_backtest(hypothesis(), bars([10, 20, 30, 40]), SmaCrossStrategy(1, 2))
        second = run_backtest(hypothesis(), bars([10, 20, 30, 1]), SmaCrossStrategy(1, 2))
        self.assertEqual(first.trades[0].entry_date, second.trades[0].entry_date)
        self.assertEqual(first.trades[0].entry_price, second.trades[0].entry_price)
