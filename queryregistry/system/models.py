"""System query registry service models."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypedDict

__all__ = [
  "SystemCheckStatusCallable",
  "SystemCheckStatusPayload",
]


class SystemCheckStatusPayload(TypedDict):
  status: str
  provider: str


SystemCheckStatusCallable = Callable[[], Awaitable["SystemCheckStatusPayload"]]
