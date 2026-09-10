import sqlite3
import tempfile
import unittest
from pathlib import Path

from quant_lab.backtester import run_backtest
from quant_lab.registry import ExperimentRegistry
from quant_lab.strategies import SmaCrossStrategy

from conftest import bars, hypothesis


class RegistryTests(unittest.TestCase):
    def test_registry_persists_a_paper_experiment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lab.db"
            h = hypothesis()
            result = run_backtest(h, bars([10, 11, 12, 11]), SmaCrossStrategy(1, 2))
            experiment_id = ExperimentRegistry(path).save(h, b"source-data", result)
            db = sqlite3.connect(path)
            self.assertEqual(db.execute("SELECT mode FROM experiments WHERE id=?", (experiment_id,)).fetchone(), ("PAPER",))
            self.assertGreaterEqual(db.execute("SELECT COUNT(*) FROM metrics WHERE experiment_id=?", (experiment_id,)).fetchone()[0], 8)
