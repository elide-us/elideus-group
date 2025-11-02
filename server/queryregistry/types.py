"""Shared type definitions for QueryRegistry dispatchers."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from .models import DBRequest, DBResponse

__all__ = [
  "CheckStatusCallable",
  "CheckStatusPayload",
  "SubdomainDispatcher",
]

CheckStatusPayload = Mapping[str, Any]


class CheckStatusCallable(Protocol):
  async def __call__(self) -> CheckStatusPayload: ...


class SubdomainDispatcher(Protocol):
  async def __call__(self, request: DBRequest, *, provider: str) -> DBResponse: ...
