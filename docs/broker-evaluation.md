# Broker evaluation for Quant Lab

Research date: 2026-09-10

## Decision

Use Interactive Brokers (IBKR) as the first broker and keep the integration
strictly PAPER-only during validation. The initial adapter targets the local
Client Portal Gateway for account checks, positions, order previews, and a
guarded paper-order API. A future unattended worker should use a separately
reviewed TWS/IB Gateway adapter; Client Portal Gateway authentication requires
regular interactive reauthentication.

## Why IBKR

- The Czech Republic is explicitly present in IBKR's account-opening country
  list.
- IBKR paper accounts are supported by both the Web API and TWS API.
- The same account can later support a controlled migration from simulation,
  without designing the research system around a paper-only vendor.
- Mature open-source systems already implement this model. QuantConnect LEAN
  supports IBKR and other brokers, while NautilusTrader provides an IBKR adapter
  for data and execution through TWS or IB Gateway.

## Alternatives considered

### Alpaca

Alpaca offers convenient global paper-only accounts and a simple paper/live API.
The free market-data plan is IEX-only, and the paper simulator does not model all
live effects. Current official material reviewed for this decision did not give
us sufficiently clear Czech live-account eligibility, so it remains a useful
secondary adapter rather than the first broker.

### Saxo OpenAPI

Saxo provides separate SIM and LIVE environments. A direct-client live
application requires a funded account, prior SIM testing, and Saxo approval.
This is viable later, but adds more onboarding friction for the first milestone.

## Safety boundary

The shipped adapter accepts only HTTPS loopback gateway URLs and `DU` paper
account IDs. It permits only long-only DAY market or limit orders, applies an
order-size cap, defaults order submission to disabled, and never confirms broker
warnings automatically. The CLI exposes connection checks and `whatif` previews,
not order submission. Quant Lab never reads or stores IBKR credentials.

## Primary references

- [IBKR available countries](https://www.interactivebrokers.com/en/accounts/open-account-country-list.php)
- [IBKR Web API documentation](https://ibkrcampus.com/campus/ibkr-api-page/webapi-doc/)
- [Client Portal Gateway authentication FAQ](https://ibkrcampus.com/docs/web-api/authentication/cpgw/client-portal-gateway-faq)
- [IBKR paper trading account](https://ibkrcampus.com/campus/glossary-terms/paper-trading-account/)
- [IBKR order preview endpoint](https://ibkrcampus.com/docs/web-api/v1/endpoints/orders/preview-order-what-if-order)
- [Alpaca paper trading](https://docs.alpaca.markets/docs/paper-trading)
- [Saxo OpenAPI environments](https://www.developer.saxo/openapi/learn/environments)
- [QuantConnect LEAN brokerages](https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages)
- [NautilusTrader IBKR integration](https://nautilustrader.io/docs/latest/integrations/interactive_brokers/)
