from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .models import Bar


class Strategy(ABC):
    """A strategy emits close-derived targets executed on the next bar's open."""

    @abstractmethod
    def target_weights(self, bars: list[Bar]) -> list[float]:
        raise NotImplementedError


@dataclass(frozen=True)
class SmaCrossStrategy(Strategy):
    fast: int
    slow: int

    def __post_init__(self) -> None:
        if self.fast < 1 or self.slow <= self.fast:
            raise ValueError("Require 1 <= fast < slow")

    def target_weights(self, bars: list[Bar]) -> list[float]:
        closes = [bar.close for bar in bars]
        targets: list[float] = []
        for i in range(len(closes)):
            if i + 1 < self.slow:
                targets.append(0.0)
                continue
            fast_avg = sum(closes[i + 1 - self.fast : i + 1]) / self.fast
            slow_avg = sum(closes[i + 1 - self.slow : i + 1]) / self.slow
            targets.append(1.0 if fast_avg > slow_avg else 0.0)
        return targets


def strategy_from(name: str, parameters: dict[str, object]) -> Strategy:
    if name == "sma_cross":
        return SmaCrossStrategy(fast=int(parameters["fast"]), slow=int(parameters["slow"]))
    raise ValueError(f"Unsupported strategy: {name}")

