from __future__ import annotations

import json
import ssl
from typing import Callable, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import Broker, BrokerAccount, OrderRequest, OrderResult, Position

Transport = Callable[[str, str, Optional[object]], object]


class PaperSafetyError(RuntimeError):
    pass


class ManualConfirmationRequired(RuntimeError):
    def __init__(self, confirmation_id: str, messages: list[str]) -> None:
        super().__init__("IBKR requires manual order confirmation: " + " ".join(messages))
        self.confirmation_id = confirmation_id
        self.messages = messages


def _validate_loopback_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise PaperSafetyError("IBKR PAPER adapter only permits an HTTPS loopback gateway URL")
    return base_url.rstrip("/")


class IbkrPaperBroker(Broker):
    """Minimal Client Portal Gateway adapter locked to IBKR simulated accounts."""

    def __init__(
        self,
        account_id: str,
        base_url: str = "https://localhost:5000/v1/api",
        *,
        allow_order_submission: bool = False,
        verify_local_tls: bool = True,
        max_order_quantity: float = 100.0,
        transport: Transport | None = None,
    ) -> None:
        if not account_id.startswith("DU"):
            raise PaperSafetyError("IBKR paper account IDs must start with DU")
        if max_order_quantity <= 0:
            raise ValueError("max_order_quantity must be positive")
        self.account_id = account_id
        self.base_url = _validate_loopback_url(base_url)
        self.allow_order_submission = allow_order_submission
        self.max_order_quantity = max_order_quantity
        self._transport = transport or self._http_transport(verify_local_tls)

    def _http_transport(self, verify_local_tls: bool) -> Transport:
        context = None
        if not verify_local_tls:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        def request(method: str, path: str, payload: object | None = None) -> object:
            body = None if payload is None else json.dumps(payload).encode("utf-8")
            req = Request(
                self.base_url + path,
                data=body,
                method=method,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            with urlopen(req, context=context, timeout=15) as response:
                content = response.read()
            return json.loads(content) if content else {}

        return request

    def _request(self, method: str, path: str, payload: object | None = None) -> object:
        return self._transport(method, path, payload)

    def account(self) -> BrokerAccount:
        status = self._request("GET", "/iserver/auth/status")
        if not isinstance(status, dict) or not status.get("authenticated"):
            raise PaperSafetyError("IBKR gateway is not authenticated")
        accounts = self._request("GET", "/iserver/accounts")
        account_ids = accounts.get("accounts", []) if isinstance(accounts, dict) else []
        if self.account_id not in account_ids:
            raise PaperSafetyError(
                "Configured paper account is not available in this gateway session"
            )
        return BrokerAccount(self.account_id, "PAPER")

    def positions(self) -> list[Position]:
        self.account()
        self._request("GET", "/portfolio/accounts")
        rows = self._request("GET", f"/portfolio2/{self.account_id}/positions")
        if not isinstance(rows, list):
            raise RuntimeError("Unexpected IBKR positions response")
        return [
            Position(
                conid=int(row["conid"]),
                symbol=str(row.get("description", row.get("contractDesc", ""))),
                quantity=float(row["position"]),
                market_value=float(row.get("marketValue", row.get("mktValue", 0.0))),
                currency=str(row.get("currency", "")),
            )
            for row in rows
        ]

    def _validate_order(self, order: OrderRequest) -> None:
        if order.side not in {"BUY", "SELL"}:
            raise PaperSafetyError("Only BUY and SELL are supported")
        if order.order_type not in {"MKT", "LMT"}:
            raise PaperSafetyError("Only MKT and LMT orders are supported")
        if order.time_in_force != "DAY":
            raise PaperSafetyError("Only DAY orders are supported")
        if order.quantity <= 0 or order.quantity > self.max_order_quantity:
            raise PaperSafetyError("Order quantity is outside configured PAPER limits")
        if order.order_type == "LMT" and (order.limit_price is None or order.limit_price <= 0):
            raise PaperSafetyError("A positive limit price is required for LMT orders")
        if order.side == "SELL":
            held = next((p.quantity for p in self.positions() if p.conid == order.conid), 0.0)
            if order.quantity > held:
                raise PaperSafetyError("SELL would create a short position")

    def _payload(self, order: OrderRequest) -> dict[str, object]:
        payload: dict[str, object] = {
            "acctId": self.account_id,
            "conid": order.conid,
            "side": order.side,
            "quantity": order.quantity,
            "orderType": order.order_type,
            "tif": order.time_in_force,
            "manualIndicator": False,
        }
        if order.limit_price is not None:
            payload["price"] = order.limit_price
        if order.client_order_id is not None:
            payload["cOID"] = order.client_order_id
        return payload

    def preview_order(self, order: OrderRequest) -> dict[str, object]:
        self._validate_order(order)
        self.account()
        result = self._request(
            "POST",
            f"/iserver/account/{self.account_id}/orders/whatif",
            {"orders": [self._payload(order)]},
        )
        if not isinstance(result, dict):
            raise RuntimeError("Unexpected IBKR preview response")
        return result

    def submit_order(self, order: OrderRequest) -> OrderResult:
        if not self.allow_order_submission:
            raise PaperSafetyError("Order submission is disabled; use preview_order first")
        self._validate_order(order)
        self.account()
        result = self._request(
            "POST", f"/iserver/account/{self.account_id}/orders", {"orders": [self._payload(order)]}
        )
        first = result[0] if isinstance(result, list) and result else result
        if not isinstance(first, dict):
            raise RuntimeError("Unexpected IBKR order response")
        if "error" in first:
            raise RuntimeError(str(first["error"]))
        if "id" in first and "message" in first:
            raise ManualConfirmationRequired(str(first["id"]), list(first["message"]))
        order_id = first.get("order_id")
        if order_id is None:
            raise RuntimeError("IBKR response did not contain an order ID")
        return OrderResult(str(order_id), str(first.get("order_status", "UNKNOWN")))

    def cancel_order(self, order_id: str) -> dict[str, object]:
        if not self.allow_order_submission:
            raise PaperSafetyError("Order mutation is disabled")
        self.account()
        result = self._request("DELETE", f"/iserver/account/{self.account_id}/order/{order_id}")
        if not isinstance(result, dict):
            raise RuntimeError("Unexpected IBKR cancellation response")
        return result

    def order_status(self, order_id: str) -> dict[str, object]:
        self.account()
        result = self._request("GET", f"/iserver/account/order/status/{order_id}")
        if not isinstance(result, dict):
            raise RuntimeError("Unexpected IBKR order status response")
        return result
