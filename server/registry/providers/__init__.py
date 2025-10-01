"""Provider dispatch helpers for the registry."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping

from server.registry.types import DBRequest, DBResponse

ProviderCallable = Callable[[DBRequest], Awaitable[DBResponse]]
ProviderQueryMap = Mapping[str, Mapping[int, ProviderCallable] | ProviderCallable]

__all__ = [
  "ProviderCallable",
  "ProviderQueryMap",
]
