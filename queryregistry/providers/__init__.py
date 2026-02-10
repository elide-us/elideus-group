"""Queryregistry provider helpers."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
import importlib
from typing import Any

_PROVIDER_NAMES = ("mssql", "mysql", "postgres")


def _load_provider(name: str) -> Any:
  return importlib.import_module(f"{__name__}.{name}")


class ProviderRegistry(Mapping[str, Any]):
  def __getitem__(self, key: str) -> Any:
    if key not in _PROVIDER_NAMES:
      raise KeyError(key)
    return _load_provider(key)

  def __iter__(self) -> Iterator[str]:
    return iter(_PROVIDER_NAMES)

  def __len__(self) -> int:
    return len(_PROVIDER_NAMES)


def __getattr__(name: str) -> Any:
  if name in _PROVIDER_NAMES:
    module = _load_provider(name)
    globals()[name] = module
    return module
  raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


PROVIDERS = ProviderRegistry()

__all__ = ["PROVIDERS", "mssql", "mysql", "postgres"]
