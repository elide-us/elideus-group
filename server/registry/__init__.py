"""Database registry scaffolding for DBRequest dispatch."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Mapping

from .models import DBRequest

logger = logging.getLogger(__name__)

__all__ = [
  "HandlerInfo",
  "RegistryRouter",
  "get_handler",
  "get_handler_info",
  "parse_db_op",
]


@dataclass(slots=True)
class _HandlerSpec:
  module: str
  attribute: str
  legacy: bool = False
  cached: Callable[[Mapping[str, Any]], Any] | None = None

  def load(self) -> Callable[[Mapping[str, Any]], Any]:
    if self.cached is None:
      module = import_module(self.module)
      self.cached = getattr(module, self.attribute)
    return self.cached


@dataclass(slots=True)
class HandlerInfo:
  _spec: _HandlerSpec

  @property
  def legacy(self) -> bool:
    return self._spec.legacy

  def load(self) -> Callable[[Mapping[str, Any]], Any]:
    return self._spec.load()


class _HandlerRegistry:
  def __init__(self) -> None:
    self._providers: Dict[str, Dict[str, _HandlerSpec]] = {}

  def register(
    self,
    provider: str,
    op: str,
    *,
    module: str,
    attribute: str,
    legacy: bool = False,
  ) -> None:
    provider_map = self._providers.setdefault(provider, {})
    if op in provider_map:
      raise ValueError(f"Duplicate handler registration for {op}")
    provider_map[op] = _HandlerSpec(module=module, attribute=attribute, legacy=legacy)

  def get_spec(self, op: str, *, provider: str) -> _HandlerSpec:
    try:
      return self._providers[provider][op]
    except KeyError as exc:
      raise KeyError(
        f"No handler registered for operation '{op}' with provider '{provider}'"
      ) from exc
 
  def get(self, op: str, *, provider: str) -> Callable[[Mapping[str, Any]], Any]:
    return self.get_spec(op, provider=provider).load()


def parse_db_op(op: str) -> tuple[str, tuple[str, ...], int]:
  parts = op.split(":")
  if len(parts) < 4 or parts[0] != "db":
    raise ValueError(f"Invalid database operation: {op}")
  *segments, version_str = parts[1:]
  try:
    version = int(version_str)
  except ValueError as exc:
    raise ValueError(f"Invalid DB operation version: {op}") from exc
  domain, *path = segments
  return domain, tuple(path), version


class RegistryRouter:
  def __init__(self, *, provider: str = "mssql") -> None:
    self._registry = _HandlerRegistry()
    self._provider = provider

  @property
  def provider(self) -> str:
    return self._provider

  def register_function(
    self,
    *,
    domain: str,
    path: tuple[str, ...] = (),
    name: str,
    version: int = 1,
    implementation: str | None = None,
    provider: str | None = None,
    legacy: bool = False,
    op_path: tuple[str, ...] | None = None,
  ) -> None:
    func = implementation or name
    effective_op_path = op_path if op_path is not None else path
    op_segments = ("db", domain, *effective_op_path, name, str(version))
    op = ":".join(segment for segment in op_segments if segment)
    module_components = (domain, *path)
    module = ".".join((__name__, *module_components, self._provider))
    attribute = f"{func}_v{version}"
    self._registry.register(
      provider or self._provider,
      op,
      module=module,
      attribute=attribute,
      legacy=legacy,
    )

  def get_handler(self, op: str) -> Callable[[Mapping[str, Any]], Any]:
    return self._registry.get(op, provider=self._provider)


_registry_router = RegistryRouter()

from . import account, finance, system  # noqa: E402

finance.register(_registry_router)
account.register(_registry_router)
system.register(_registry_router)


def _lookup_handler_spec(op: str, *, provider: str) -> _HandlerSpec:
  try:
    return _registry_router._registry.get_spec(op, provider=provider)
  except KeyError:
    logger.error(
      "Registry handler resolution failed",
      extra={"db_op": op, "db_provider": provider},
      exc_info=False,
    )
    raise


def get_handler(op: str, *, provider: str = "mssql") -> Callable[[Mapping[str, Any]], Any]:
  spec = _lookup_handler_spec(op, provider=provider)
  logger.info(
    "Registry handler resolved",
    extra={"db_op": op, "db_provider": provider},
  )
  return spec.load()


def get_handler_info(
  op: str,
  *,
  provider: str = "mssql",
  log_resolution: bool = True,
) -> HandlerInfo:
  spec = _lookup_handler_spec(op, provider=provider)
  if log_resolution:
    logger.info(
      "Registry handler resolved",
      extra={"db_op": op, "db_provider": provider},
    )
  return HandlerInfo(_spec=spec)
