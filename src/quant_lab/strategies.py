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


@dataclass(frozen=True)
class BuyAndHoldStrategy(Strategy):
    def target_weights(self, bars: list[Bar]) -> list[float]:
        return [1.0] * len(bars)


@dataclass(frozen=True)
class MomentumStrategy(Strategy):
    lookback: int = 20
    skip: int = 0

    def __post_init__(self) -> None:
        if self.lookback < 1 or self.skip < 0:
            raise ValueError("Require lookback >= 1 and skip >= 0")

    def target_weights(self, bars: list[Bar]) -> list[float]:
        closes = [bar.close for bar in bars]
        targets = [0.0] * len(bars)
        for i in range(self.lookback + self.skip, len(bars)):
            recent = closes[i - self.skip]
            past = closes[i - self.skip - self.lookback]
            targets[i] = 1.0 if recent > past else 0.0
        return targets


@dataclass(frozen=True)
class MeanReversionStrategy(Strategy):
    lookback: int = 5
    entry_drop: float = 0.03

    def __post_init__(self) -> None:
        if self.lookback < 1 or self.entry_drop <= 0:
            raise ValueError("Require lookback >= 1 and entry_drop > 0")

    def target_weights(self, bars: list[Bar]) -> list[float]:
        closes = [bar.close for bar in bars]
        targets = [0.0] * len(bars)
        for i in range(self.lookback, len(bars)):
            change = closes[i] / closes[i - self.lookback] - 1.0
            targets[i] = 1.0 if change <= -self.entry_drop + 1e-12 else 0.0
        return targets


def strategy_from(name: str, parameters: dict[str, object]) -> Strategy:
    if name == "sma_cross":
        return SmaCrossStrategy(fast=int(parameters["fast"]), slow=int(parameters["slow"]))
    if name == "buy_and_hold":
        return BuyAndHoldStrategy()
    if name == "momentum":
        return MomentumStrategy(
            lookback=int(parameters.get("lookback", 20)),
            skip=int(parameters.get("skip", 0)),
        )
    if name == "mean_reversion":
        return MeanReversionStrategy(
            lookback=int(parameters.get("lookback", 5)),
            entry_drop=float(parameters.get("entry_drop", 0.03)),
        )
    raise ValueError(f"Unsupported strategy: {name}")
