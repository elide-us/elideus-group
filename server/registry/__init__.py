"""Registry dispatcher bridge."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import pkgutil
from collections.abc import Awaitable, Callable, Iterable, Mapping

from server.modules.providers import DBResult, DbProviderBase, get_dbresult_cls

from .providers import ProviderDescriptor
from .types import DBRequest, DBResponse

__all__ = [
  "DBRequest",
  "DBResponse",
  "DBResult",
  "DomainRouter",
  "ProviderBinding",
  "RegistryDispatcher",
  "RegistryRouter",
  "SubdomainRouter",
]


Executor = Callable[[DBRequest], Awaitable[DBResponse]]
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


@dataclass(slots=True)
class ProviderBinding:
  canonical: str
  provider_map: str
  version: int
  descriptor: ProviderDescriptor | None


class RegistryRouter:
  """Hierarchical router that registers domain and subdomain functions."""

  def __init__(self, *, default_provider: str | None = None):
    self._domains: dict[str, DomainRouter] = {}
    self._routes: dict[str, FunctionRoute] = {}
    self._aliases: dict[str, str] = {}
    self._initialised = False
    self._provider_name = default_provider
    self._provider_module = None
    self._provider_queries: dict[str, Mapping[int, Executor] | Executor] = {}
    self._provider_executors: dict[str, Executor] = {}
    self._provider_bindings: dict[str, ProviderBinding] = {}

  def domain(self, name: str) -> "DomainRouter":
    if name not in self._domains:
      self._domains[name] = DomainRouter(self, name)
    return self._domains[name]

  def add_route(self, route: FunctionRoute) -> None:
    key = route.key
    if key in self._routes:
      raise ValueError(f"Duplicate registry route registered: {key}")
    self._routes[key] = route
    self._attach_provider_callable(route)

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

  @property
  def provider_name(self) -> str | None:
    return self._provider_name

  def set_provider(self, name: str) -> None:
    if not name:
      raise ValueError("Provider name cannot be empty")
    if name != self._provider_name:
      self._provider_name = name
      self._provider_module = None
      self._provider_queries = {}
      self._provider_executors.clear()

  def load_provider(self, provider: str | None = None) -> None:
    name = provider or self._provider_name
    if not name:
      raise ValueError("Registry provider is not configured")
    if self._provider_module and name == self._provider_name and self._provider_queries:
      return
    module = importlib.import_module(f"server.registry.providers.{name}")
    build = getattr(module, "build_provider_queries", None)
    if callable(build):
      queries = build(self._provider_bindings.values())
    else:
      queries = getattr(module, "PROVIDER_QUERIES", None)
    if not isinstance(queries, dict):
      raise ValueError(f"Provider module '{name}' missing PROVIDER_QUERIES mapping")
    self._provider_name = name
    self._provider_module = module
    self._provider_queries = queries
    self._provider_executors.clear()
    for route in self._routes.values():
      self._attach_provider_callable(route)

  @property
  def provider_bindings(self) -> Mapping[str, ProviderBinding]:
    return self._provider_bindings

  def register_provider_binding(
    self,
    route: FunctionRoute,
    provider: ProviderDescriptor | None,
  ) -> None:
    self._provider_bindings[route.key] = ProviderBinding(
      canonical=route.key,
      provider_map=route.provider_map,
      version=route.version,
      descriptor=provider,
    )

  def get_executor(self, route: FunctionRoute) -> Executor | None:
    executor = self._provider_executors.get(route.key)
    if executor:
      return executor
    self._attach_provider_callable(route)
    return self._provider_executors.get(route.key)

  def _attach_provider_callable(self, route: FunctionRoute) -> None:
    if not self._provider_queries:
      return
    entry = self._provider_queries.get(route.provider_map)
    if entry is None:
      return
    if isinstance(entry, Mapping):
      provider_callable = entry.get(route.version)
    else:
      provider_callable = entry
    if provider_callable is None:
      return
    if not callable(provider_callable):
      raise TypeError(
        f"Provider mapping for '{route.provider_map}' version {route.version} is not callable"
      )
    self._provider_executors[route.key] = provider_callable


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
    provider: ProviderDescriptor | None = None,
  ) -> None:
    route = FunctionRoute(
      domain=self._domain.name,
      subdomain=self._name,
      name=name,
      version=version,
      provider_map=provider_map,
    )
    self._registry.add_route(route)
    self._registry.register_provider_binding(route, provider)
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

  def bind_provider(self, provider: DbProviderBase, *, provider_name: str | None = None) -> None:
    self.initialise()
    provider_key = provider_name or self.router.provider_name
    if provider_key:
      self.router.set_provider(provider_key)
      self.router.load_provider(provider_key)
    DBResultCls = get_dbresult_cls()

    def _ensure_response(result: DBResponse | DBResult | object) -> DBResponse:
      if isinstance(result, DBResponse):
        return result
      if isinstance(result, DBResultCls):
        return DBResponse.from_result(result)
      payload = result.model_dump() if hasattr(result, "model_dump") else result
      validated = DBResultCls.model_validate(payload)
      return DBResponse.from_result(validated)

    async def _execute(request: DBRequest) -> DBResponse:
      route = self.router.resolve(request.op)
      if not route:
        result = await provider.run(request.op, request.params)
        return _ensure_response(result)
      if route.key != request.op:
        request = request.model_copy(update={"op": route.key})
      executor = self.router.get_executor(route)
      if not executor:
        raise KeyError(
          f"No provider callable registered for '{route.provider_map}' version {route.version}"
        )
      result = await executor(request)
      return _ensure_response(result)

    self.set_executor(_execute)

  async def execute(self, request: DBRequest) -> DBResponse:
    if not self._executor:
      raise RuntimeError("Registry dispatcher is not configured")
    self.initialise()
    route = self.router.resolve(request.op)
    if route and route.key != request.op:
      request = request.model_copy(update={"op": route.key})
    return await self._executor(request)
