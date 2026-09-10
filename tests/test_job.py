import json
import tempfile
import unittest
from pathlib import Path

from quant_lab.runner import run_job


class JobTests(unittest.TestCase):
    def test_rejects_any_non_paper_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "job.json"
            path.write_text(json.dumps({"mode": "LIVE", "runs": [{}]}))
            with self.assertRaisesRegex(ValueError, "PAPER"):
                run_job(path)
