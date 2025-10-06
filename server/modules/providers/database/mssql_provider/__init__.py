# providers/database/mssql_provider/__init__.py
from typing import Any, Dict
from collections.abc import Mapping
import inspect

from ... import DbProviderBase, DBResult
from .logic import init_pool, close_pool
from .db_helpers import run_operation

from importlib import import_module

from server.registry.types import DBRequest, DBResponse


def _load_provider_queries(bindings=None):
  module = import_module("server.registry.providers.mssql")
  if bindings is None:
    return getattr(module, "PROVIDER_QUERIES")
  build = getattr(module, "build_provider_queries")
  return build(bindings)


class MssqlProvider(DbProviderBase):
  def __init__(self, **config: Any):
    self._provider_bindings = config.pop("provider_bindings", None)
    self._provider_queries = config.pop("provider_query_map", None)
    super().__init__(**config)

  async def startup(self) -> None:
    await init_pool(**self.config)
    if self._provider_queries is None:
      self._provider_queries = _load_provider_queries(self._provider_bindings)

  async def shutdown(self) -> None:
    await close_pool()
    # retain cached bindings for potential warm restarts

  def _resolve_provider_callable(self, op: str):
    provider_queries = self._provider_queries
    if provider_queries is None:
      provider_queries = self._provider_queries = _load_provider_queries(self._provider_bindings)
    parts = op.split(":")
    if len(parts) != 5 or parts[0] != "db":
      raise KeyError(f"Unsupported operation key: {op}")
    _, domain, subdomain, name, version_str = parts
    try:
      version = int(version_str)
    except ValueError as exc:
      raise KeyError(f"Invalid operation version for '{op}'") from exc
    provider_map = f"{domain}.{subdomain}.{name}"
    entry = provider_queries.get(provider_map)
    if entry is None:
      raise KeyError(f"No MSSQL handler for '{op}'")
    if isinstance(entry, Mapping):
      handler = entry.get(version)
    else:
      handler = entry
    if handler is None:
      raise KeyError(f"No MSSQL handler for '{op}' version {version}")
    if not callable(handler):
      raise TypeError(
        f"Provider mapping for '{provider_map}' version {version} is not callable"
      )
    return handler

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    handler = self._resolve_provider_callable(op)
    request = DBRequest(op=op, params=args)
    response = handler(request)
    if inspect.isawaitable(response):
      response = await response
    if not isinstance(response, DBResponse):
      raise TypeError(
        f"Handler '{op}' returned unsupported result type: {type(response)!r}."
        " Expected DBResponse."
      )
    return response.to_result(result_cls=DBResult)
