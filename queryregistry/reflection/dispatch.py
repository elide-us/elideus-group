"""Shared protocol helpers for reflection subdomain dispatchers."""

from __future__ import annotations

from typing import Protocol

from queryregistry.models import DBRequest, DBResponse

__all__ = ["SubdomainDispatcher"]


class SubdomainDispatcher(Protocol):
  async def __call__(self, request: DBRequest, *, provider: str) -> DBResponse: ...
