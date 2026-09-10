import unittest

from quant_lab.models import DatasetSplit, GateRules
from quant_lab.strategies import BuyAndHoldStrategy
from quant_lab.validation import gate, split_bars, validate_strategy

from conftest import bars, hypothesis


class ValidationTests(unittest.TestCase):
    def test_splits_are_chronological_and_disjoint(self):
        data = bars(list(range(10, 40)))
        parts = split_bars(data, DatasetSplit(0.5, 0.25))
        self.assertEqual([len(parts[s]) for s in ("TRAIN", "VALIDATION", "VAULT")], [15, 7, 8])
        self.assertLess(parts["TRAIN"][-1].date, parts["VALIDATION"][0].date)
        self.assertLess(parts["VALIDATION"][-1].date, parts["VAULT"][0].date)

    def test_pipeline_stops_before_validation_when_train_fails(self):
        data = bars([10.0] * 30)
        report = validate_strategy(hypothesis(strategy="buy_and_hold", parameters={}), data, BuyAndHoldStrategy())
        self.assertEqual(report.status, "REJECTED")
        self.assertEqual(set(report.stages), {"TRAIN"})

    def test_lenient_gates_allow_all_stages(self):
        data = bars([float(x) for x in range(10, 70)])
        lenient = GateRules(min_trades=1, min_sharpe=-100, max_drawdown=1, min_profit_factor=0, must_be_profitable=False)
        report = validate_strategy(
            hypothesis(strategy="buy_and_hold", parameters={}),
            data,
            BuyAndHoldStrategy(),
            rules={stage: lenient for stage in ("TRAIN", "VALIDATION", "VAULT")},
        )
        self.assertEqual(report.status, "VAULT_PASS")
        self.assertEqual(set(report.stages), {"TRAIN", "VALIDATION", "VAULT"})

    def test_gate_rejects_large_drawdown(self):
        metrics = {"trade_count": 30, "sharpe": 1, "max_drawdown": -0.4, "profit_factor": 2, "total_return": 0.1}
        self.assertEqual(gate(metrics, GateRules()), "drawdown above threshold")
