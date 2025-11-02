"""Account query registry service models."""

from __future__ import annotations

from typing import TypedDict

from server.queryregistry.types import CheckStatusCallable

__all__ = [
  "AccountCheckStatusCallable",
  "AccountCheckStatusPayload",
]


class AccountCheckStatusPayload(TypedDict):
  status: str
  provider: str


AccountCheckStatusCallable = CheckStatusCallable
