"""Database registry scaffolding for DBRequest dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Mapping

from .models import DBRequest

__all__ = [
  "DomainRouter",
  "RegistryRouter",
  "SubdomainRouter",
  "get_handler",
  "parse_db_op",
]


@dataclass(slots=True)
class _HandlerSpec:
  module: str
  attribute: str
  cached: Callable[[Mapping[str, Any]], Any] | None = None

  def load(self) -> Callable[[Mapping[str, Any]], Any]:
    if self.cached is None:
      module = import_module(self.module)
      self.cached = getattr(module, self.attribute)
    return self.cached


class _HandlerRegistry:
  def __init__(self) -> None:
    self._providers: Dict[str, Dict[str, _HandlerSpec]] = {}

  def register(self, provider: str, op: str, *, module: str, attribute: str) -> None:
    provider_map = self._providers.setdefault(provider, {})
    if op in provider_map:
      raise ValueError(f"Duplicate handler registration for {op}")
    provider_map[op] = _HandlerSpec(module=module, attribute=attribute)

  def get(self, op: str, *, provider: str) -> Callable[[Mapping[str, Any]], Any]:
    try:
      spec = self._providers[provider][op]
    except KeyError as exc:
      raise KeyError(f"Handler for {op} not found") from exc
    return spec.load()


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

  def domain(self, name: str) -> "DomainRouter":
    return DomainRouter(self._registry, name, provider=self._provider)

  def get_handler(self, op: str) -> Callable[[Mapping[str, Any]], Any]:
    return self._registry.get(op, provider=self._provider)


class DomainRouter:
  def __init__(self, registry: _HandlerRegistry, name: str, *, provider: str) -> None:
    self._registry = registry
    self._name = name
    self._provider = provider
    self._components: tuple[str, ...] = (name,)

  @property
  def name(self) -> str:
    return self._name

  def subdomain(self, name: str, *, op_segment: str | None = None) -> "SubdomainRouter":
    segment = op_segment or name
    components = self._components + (name,)
    op_path = (segment,)
    return SubdomainRouter(self._registry, self._name, components, op_path, provider=self._provider)

  def add_function(
    self,
    name: str,
    *,
    version: int = 1,
    implementation: str | None = None,
  ) -> None:
    router = SubdomainRouter(self._registry, self._name, self._components, (), provider=self._provider)
    router.add_function(name, version=version, implementation=implementation)


class SubdomainRouter:
  def __init__(
    self,
    registry: _HandlerRegistry,
    domain: str,
    module_components: tuple[str, ...],
    op_path: tuple[str, ...],
    *,
    provider: str,
  ) -> None:
    self._registry = registry
    self._domain = domain
    self._module_components = module_components
    self._op_path = op_path
    self._provider = provider

  def subdomain(self, name: str, *, op_segment: str | None = None) -> "SubdomainRouter":
    segment = op_segment or name
    module_components = self._module_components + (name,)
    op_path = self._op_path + (segment,)
    return SubdomainRouter(
      self._registry,
      self._domain,
      module_components,
      op_path,
      provider=self._provider,
    )

  def add_function(
    self,
    name: str,
    *,
    version: int = 1,
    implementation: str | None = None,
    provider: str | None = None,
  ) -> None:
    func = implementation or name
    op_segments = ("db", self._domain, *self._op_path, name, str(version))
    op = ":".join(segment for segment in op_segments if segment)
    module = ".".join((__name__, *self._module_components, self._provider))
    attribute = f"{func}_v{version}"
    self._registry.register(provider or self._provider, op, module=module, attribute=attribute)


_registry_router = RegistryRouter()

from . import auth, finance, system, users  # noqa: E402

finance.register(_registry_router)
auth.register(_registry_router)
system.register(_registry_router)
users.register(_registry_router)


def get_handler(op: str, *, provider: str = "mssql") -> Callable[[Mapping[str, Any]], Any]:
  try:
    if provider == _registry_router.provider:
      return _registry_router.get_handler(op)
    return _registry_router._registry.get(op, provider=provider)
  except KeyError:
    if provider == "mssql":
      from server.modules.providers.database.mssql_provider.registry import get_handler as legacy_get_handler

      return legacy_get_handler(op)
    raise
