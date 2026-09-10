import math
import unittest

from quant_lab.metrics import cagr, max_drawdown, sharpe_ratio


class MetricTests(unittest.TestCase):
    def test_max_drawdown(self):
        self.assertTrue(math.isclose(max_drawdown([100, 120, 90, 110]), -0.25))

    def test_cagr_one_year(self):
        self.assertTrue(math.isclose(cagr([100] + [100] * 251 + [110]), 0.10))

    def test_flat_sharpe_is_zero(self):
        self.assertEqual(sharpe_ratio([100, 100, 100]), 0)
