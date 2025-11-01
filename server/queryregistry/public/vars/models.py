"""Public vars query registry service models."""

from __future__ import annotations

from typing import TypedDict

from server.queryregistry.types import CheckStatusCallable

__all__ = [
  "PublicVarsCheckStatusCallable",
  "PublicVarsCheckStatusPayload",
]


class PublicVarsCheckStatusPayload(TypedDict):
  status: str
  provider: str


PublicVarsCheckStatusCallable = CheckStatusCallable
