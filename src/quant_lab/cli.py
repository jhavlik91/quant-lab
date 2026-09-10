from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .brokers import IbkrPaperBroker, OrderRequest
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
    broker_check = sub.add_parser("broker-check", help="Check an authenticated IBKR PAPER gateway")
    broker_check.add_argument("--account-id", required=True)
    broker_check.add_argument("--base-url", default="https://localhost:5000/v1/api")
    broker_check.add_argument("--insecure-local-tls", action="store_true")
    broker_preview = sub.add_parser(
        "broker-preview", help="Preview an IBKR PAPER order without submitting it"
    )
    broker_preview.add_argument("--account-id", required=True)
    broker_preview.add_argument("--conid", type=int, required=True)
    broker_preview.add_argument("--side", choices=("BUY", "SELL"), required=True)
    broker_preview.add_argument("--quantity", type=float, required=True)
    broker_preview.add_argument("--order-type", choices=("MKT", "LMT"), default="MKT")
    broker_preview.add_argument("--limit-price", type=float)
    broker_preview.add_argument("--base-url", default="https://localhost:5000/v1/api")
    broker_preview.add_argument("--insecure-local-tls", action="store_true")
    args = parser.parse_args()
    if args.command == "run":
        output = run_one(Path(args.hypothesis), Path(args.ohlcv), Path(args.db))
    elif args.command == "job":
        output = run_job(Path(args.manifest))
    elif args.command == "validate":
        output = run_validation(Path(args.hypothesis), Path(args.ohlcv))
    elif args.command == "list":
        output = ExperimentRegistry(args.db).list_experiments(args.limit)
    elif args.command == "show":
        output = ExperimentRegistry(args.db).get_experiment(args.experiment_id)
        if output is None:
            parser.error(f"Experiment not found: {args.experiment_id}")
    elif args.command == "broker-check":
        broker = IbkrPaperBroker(
            args.account_id,
            args.base_url,
            verify_local_tls=not args.insecure_local_tls,
        )
        output = {
            "account": asdict(broker.account()),
            "positions": [asdict(position) for position in broker.positions()],
        }
    else:
        broker = IbkrPaperBroker(
            args.account_id,
            args.base_url,
            verify_local_tls=not args.insecure_local_tls,
        )
        output = broker.preview_order(
            OrderRequest(
                conid=args.conid,
                side=args.side,
                quantity=args.quantity,
                order_type=args.order_type,
                limit_price=args.limit_price,
            )
        )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
