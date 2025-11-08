"""Finance query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypedDict

__all__ = [
  "FinanceCheckStatusCallable",
  "FinanceCheckStatusPayload",
]


class FinanceCheckStatusPayload(TypedDict):
  status: str
  provider: str


FinanceCheckStatusCallable = Callable[[], Awaitable["FinanceCheckStatusPayload"]]
