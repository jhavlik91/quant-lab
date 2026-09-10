# Quant Lab v0.1

A deliberately small, deterministic and **PAPER-only** quantitative research lab.
It turns a structured JSON hypothesis plus historical OHLCV CSV data into a
reproducible backtest stored in SQLite, including trades, equity curve, fees,
slippage, Sharpe ratio, CAGR, maximum drawdown and a buy-and-hold benchmark.

This is research software, not investment advice. It contains no broker adapter,
credentials, live endpoint or order-submission capability.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python -m unittest discover -s tests
quant-lab run examples/sma_cross.json examples/sample_ohlcv.csv --db quant_lab.db
quant-lab job examples/job.json
quant-lab list --db examples/quant_lab.db
quant-lab validate examples/sma_cross.json examples/sample_ohlcv.csv
```

The command prints the experiment ID and metrics. Every run hashes its hypothesis,
input data and engine version so the result can be reproduced and audited.

## Hypothesis contract

The first supported strategy is `sma_cross`. Signals are calculated at a day's
close and executed at the **next day's open**, preventing same-bar look-ahead.

```json
{
  "id": "HYP-0001",
  "name": "SMA trend baseline",
  "strategy": "sma_cross",
  "symbol": "SAMPLE",
  "parameters": {"fast": 3, "slow": 5},
  "initial_cash": 100000,
  "fees_bps": 5,
  "slippage_bps": 10,
  "annualization_days": 252
}
```

CSV columns are `date,open,high,low,close,volume`, sorted strictly by date.

## Scope and safety

- Long-only, fully invested or cash; no leverage, shorts or options.
- No network access and no live trading code.
- Local SQLite is the MVP registry; its schema separates experiments, metrics,
  trades and equity points and can later be mapped to PostgreSQL.
- Baselines: SMA crossover and buy-and-hold benchmark.
- Baseline strategies: buy-and-hold, SMA crossover, momentum and mean reversion.
- Tests cover look-ahead behavior, costs, metrics and persistence.

## Sequential validation

`quant-lab validate` divides chronological data into disjoint TRAIN (60%),
VALIDATION (20%) and untouched VAULT (20%) segments. A strategy advances only
when the preceding segment passes minimum trade count, Sharpe, drawdown,
profit-factor and profitability gates. The resulting score is descriptive, not
a guarantee of future returns.

## Running scheduled jobs

`examples/job.json` is a manifest for one or more reproducible PAPER runs. The
included GitHub Actions workflow runs it weekly and keeps the SQLite database as
a 30-day build artifact. A Docker image is also included for a persistent worker:

```bash
docker build -t quant-lab .
docker run --rm -v "$PWD/data:/data" quant-lab job examples/job.json
```

For production, use an external PostgreSQL database before adding a web UI.
Vercel is suitable for that future UI/API, but the backtest worker should run on
a container job service: serverless local storage is temporary and research runs
can exceed request-duration limits.

## IBKR PAPER gateway

The first broker adapter targets the Interactive Brokers Client Portal Gateway.
It is deliberately restricted to `https://localhost` / `127.0.0.1`, simulated
account IDs beginning with `DU`, long-only `MKT` or `LMT` day orders, and a
configurable quantity cap. Order submission is disabled by default; `whatif`
preview is the normal first step. Broker warnings require manual confirmation
and are never auto-accepted.

No IBKR credentials are read or stored by Quant Lab. Start and authenticate the
Client Portal Gateway separately, then construct `IbkrPaperBroker` with the
paper account ID. The gateway requires regular interactive reauthentication, so
this adapter is not presented as unattended live-trading infrastructure.

After logging into the gateway with the paper username, verify the connection:

```bash
quant-lab broker-check --account-id DU1234567 --insecure-local-tls
quant-lab broker-preview --account-id DU1234567 --conid 265598 \
  --side BUY --quantity 1 --order-type LMT --limit-price 100 \
  --insecure-local-tls
```

The CLI intentionally exposes account inspection and `whatif` preview only. It
does not expose an order-submission command.
