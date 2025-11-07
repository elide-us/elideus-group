"""Account query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypedDict

__all__ = [
  "AccountCheckStatusCallable",
  "AccountCheckStatusPayload",
]


class AccountCheckStatusPayload(TypedDict):
  status: str
  provider: str


AccountCheckStatusCallable = Callable[[], Awaitable["AccountCheckStatusPayload"]]
