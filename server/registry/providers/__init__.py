"""Provider dispatch helpers for the registry."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from server.registry.types import DBRequest, DBResponse

ProviderCallable = Callable[[DBRequest], Awaitable[DBResponse]]
ProviderQueryMap = Mapping[str, Mapping[int, ProviderCallable] | ProviderCallable]
RawProvider = Callable[[dict[str, Any]], Awaitable[DBResponse] | DBResponse]
ProviderDescriptor = RawProvider | tuple[str, str]

__all__ = [
  "ProviderCallable",
  "ProviderQueryMap",
  "ProviderDescriptor",
  "RawProvider",
]
