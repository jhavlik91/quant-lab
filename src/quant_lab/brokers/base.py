from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerAccount:
    account_id: str
    mode: str


@dataclass(frozen=True)
class Position:
    conid: int
    symbol: str
    quantity: float
    market_value: float
    currency: str


@dataclass(frozen=True)
class OrderRequest:
    conid: int
    side: str
    quantity: float
    order_type: str = "MKT"
    time_in_force: str = "DAY"
    limit_price: float | None = None
    client_order_id: str | None = None


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    status: str


class Broker(ABC):
    @abstractmethod
    def account(self) -> BrokerAccount:
        raise NotImplementedError

    @abstractmethod
    def positions(self) -> list[Position]:
        raise NotImplementedError

    @abstractmethod
    def preview_order(self, order: OrderRequest) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def submit_order(self, order: OrderRequest) -> OrderResult:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def order_status(self, order_id: str) -> dict[str, object]:
        raise NotImplementedError

