"""Public links query registry service models."""

from __future__ import annotations

from typing import TypedDict

from server.queryregistry.types import CheckStatusCallable

__all__ = [
  "PublicLinksCheckStatusCallable",
  "PublicLinksCheckStatusPayload",
]


class PublicLinksCheckStatusPayload(TypedDict):
  status: str
  provider: str


PublicLinksCheckStatusCallable = CheckStatusCallable
