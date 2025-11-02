"""Finance query registry service models."""

from __future__ import annotations

from typing import TypedDict

from server.queryregistry.types import CheckStatusCallable

__all__ = [
  "FinanceCheckStatusCallable",
  "FinanceCheckStatusPayload",
]


class FinanceCheckStatusPayload(TypedDict):
  status: str
  provider: str


FinanceCheckStatusCallable = CheckStatusCallable
