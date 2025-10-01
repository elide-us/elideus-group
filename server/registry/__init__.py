"""Registry dispatcher bridge."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import pkgutil
from typing import Awaitable, Callable, Iterable

from server.modules.providers import DBResult, DbProviderBase

from .types import DBRequest, DBResponse

__all__ = [
  "DBRequest",
  "DBResponse",
  "DBResult",
  "DomainRouter",
  "RegistryDispatcher",
  "RegistryRouter",
  "SubdomainRouter",
]


Executor = Callable[[DBRequest], Awaitable[DBResponse]]


def _current_dbresult_cls():
  from server.modules.providers import DBResult as ProvidersDBResult
  return ProvidersDBResult


@dataclass(slots=True)
class FunctionRoute:
  domain: str
  subdomain: str
  name: str
  version: int
  provider_map: str

  @property
  def key(self) -> str:
    return f"db:{self.domain}:{self.subdomain}:{self.name}:{self.version}"


class RegistryRouter:
  """Hierarchical router that registers domain and subdomain functions."""

  def __init__(self):
    self._domains: dict[str, DomainRouter] = {}
    self._routes: dict[str, FunctionRoute] = {}
    self._aliases: dict[str, str] = {}
    self._initialised = False

  def domain(self, name: str) -> "DomainRouter":
    if name not in self._domains:
      self._domains[name] = DomainRouter(self, name)
    return self._domains[name]

  def add_route(self, route: FunctionRoute) -> None:
    key = route.key
    if key in self._routes:
      raise ValueError(f"Duplicate registry route registered: {key}")
    self._routes[key] = route

  def add_alias(self, alias: str, target: str) -> None:
    if alias in self._routes or alias in self._aliases:
      raise ValueError(f"Duplicate registry alias registered: {alias}")
    self._aliases[alias] = target

  def resolve(self, op: str) -> FunctionRoute | None:
    if op in self._routes:
      return self._routes[op]
    target = self._aliases.get(op)
    if target:
      return self._routes.get(target)
    return None

  def register_domains(self) -> None:
    if self._initialised:
      return
    package = importlib.import_module("server.registry")
    for _, name, ispkg in pkgutil.iter_modules(package.__path__):
      if not ispkg or name.startswith("_"):
        continue
      module = importlib.import_module(f"{package.__name__}.{name}")
      register = getattr(module, "register", None)
      if callable(register):
        register(self)
    self._initialised = True


class DomainRouter:
  """Routes functions for a specific domain."""

  def __init__(self, registry: RegistryRouter, name: str):
    self._registry = registry
    self._name = name
    self._subdomains: dict[str, SubdomainRouter] = {}

  @property
  def name(self) -> str:
    return self._name

  def subdomain(self, name: str) -> "SubdomainRouter":
    if name not in self._subdomains:
      self._subdomains[name] = SubdomainRouter(self._registry, self, name)
    return self._subdomains[name]


class SubdomainRouter:
  """Registers concrete registry functions for a subdomain."""

  def __init__(self, registry: RegistryRouter, domain: DomainRouter, name: str):
    self._registry = registry
    self._domain = domain
    self._name = name

  @property
  def domain(self) -> DomainRouter:
    return self._domain

  @property
  def name(self) -> str:
    return self._name

  def add_function(
    self,
    name: str,
    *,
    version: int,
    provider_map: str,
    aliases: Iterable[str] | None = None,
  ) -> None:
    route = FunctionRoute(
      domain=self._domain.name,
      subdomain=self._name,
      name=name,
      version=version,
      provider_map=provider_map,
    )
    self._registry.add_route(route)
    for alias in aliases or []:
      self._registry.add_alias(alias, route.key)


class RegistryDispatcher:
  """Simple dispatcher that routes :class:`DBRequest` objects."""

  def __init__(self, *, router: RegistryRouter | None = None):
    self.router = router or RegistryRouter()
    self._executor: Executor | None = None

  def initialise(self) -> None:
    self.router.register_domains()

  def set_executor(self, executor: Executor) -> None:
    self._executor = executor

  def bind_provider(self, provider: DbProviderBase) -> None:
    self.initialise()
    async def _execute(request: DBRequest) -> DBResponse:
      route = self.router.resolve(request.op)
      if route and route.key != request.op:
        request = request.model_copy(update={"op": route.key})
      result = await provider.run(request.op, request.params)
      DBResultCls = _current_dbresult_cls()
      if isinstance(result, DBResponse):
        return result
      if isinstance(result, DBResultCls):
        return result
      payload = result.model_dump() if hasattr(result, "model_dump") else result
      validated = DBResultCls.model_validate(payload)
      return DBResponse.from_result(validated)

    self.set_executor(_execute)

  async def execute(self, request: DBRequest) -> DBResponse:
    if not self._executor:
      raise RuntimeError("Registry dispatcher is not configured")
    self.initialise()
    route = self.router.resolve(request.op)
    if route and route.key != request.op:
      request = request.model_copy(update={"op": route.key})
    return await self._executor(request)
