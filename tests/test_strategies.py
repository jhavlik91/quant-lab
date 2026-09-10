import unittest

from quant_lab.strategies import BuyAndHoldStrategy, MeanReversionStrategy, MomentumStrategy

from conftest import bars


class BaselineStrategyTests(unittest.TestCase):
    def test_buy_and_hold_is_always_long(self):
        self.assertEqual(BuyAndHoldStrategy().target_weights(bars([10, 11, 12])), [1.0, 1.0, 1.0])

    def test_momentum_uses_only_lookback_data(self):
        result = MomentumStrategy(lookback=2).target_weights(bars([10, 9, 11, 8]))
        self.assertEqual(result, [0.0, 0.0, 1.0, 0.0])

    def test_mean_reversion_buys_after_configured_drop(self):
        result = MeanReversionStrategy(lookback=2, entry_drop=0.10).target_weights(bars([10, 10, 8, 9]))
        self.assertEqual(result, [0.0, 0.0, 1.0, 1.0])
