from __future__ import annotations

import argparse
import json
from pathlib import Path

from .registry import ExperimentRegistry
from .runner import run_job, run_one, run_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="PAPER-only deterministic Quant Lab")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one PAPER backtest")
    run.add_argument("hypothesis")
    run.add_argument("ohlcv")
    run.add_argument("--db", default="quant_lab.db")
    job = sub.add_parser("job", help="Run a PAPER job manifest")
    job.add_argument("manifest")
    validation = sub.add_parser("validate", help="Run sequential TRAIN/VALIDATION/VAULT gates")
    validation.add_argument("hypothesis")
    validation.add_argument("ohlcv")
    listing = sub.add_parser("list", help="List stored experiments")
    listing.add_argument("--db", default="quant_lab.db")
    listing.add_argument("--limit", type=int, default=20)
    show = sub.add_parser("show", help="Show one stored experiment")
    show.add_argument("experiment_id")
    show.add_argument("--db", default="quant_lab.db")
    args = parser.parse_args()
    if args.command == "run":
        output = run_one(Path(args.hypothesis), Path(args.ohlcv), Path(args.db))
    elif args.command == "job":
        output = run_job(Path(args.manifest))
    elif args.command == "validate":
        output = run_validation(Path(args.hypothesis), Path(args.ohlcv))
    elif args.command == "list":
        output = ExperimentRegistry(args.db).list_experiments(args.limit)
    else:
        output = ExperimentRegistry(args.db).get_experiment(args.experiment_id)
        if output is None:
            parser.error(f"Experiment not found: {args.experiment_id}")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
