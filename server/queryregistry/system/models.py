"""System query registry service models."""

from __future__ import annotations

from typing import TypedDict

from server.queryregistry.types import CheckStatusCallable

__all__ = [
  "SystemCheckStatusCallable",
  "SystemCheckStatusPayload",
]


class SystemCheckStatusPayload(TypedDict):
  status: str
  provider: str


SystemCheckStatusCallable = CheckStatusCallable
