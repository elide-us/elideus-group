# providers/database/mssql_provider/__init__.py
from typing import Any, Dict
from collections.abc import Mapping
import inspect

from ... import DbProviderBase, DBResult
from .logic import init_pool, close_pool
from .db_helpers import Operation, execute_operation

from importlib import import_module

from server.registry.types import DBRequest, DBResponse


def _get_provider_queries():
  module = import_module("server.registry.providers.mssql")
  return getattr(module, "PROVIDER_QUERIES")


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  def _resolve_provider_callable(self, op: str):
    parts = op.split(":")
    if len(parts) != 5 or parts[0] != "db":
      raise KeyError(f"Unsupported operation key: {op}")
    _, domain, subdomain, name, version_str = parts
    try:
      version = int(version_str)
    except ValueError as exc:
      raise KeyError(f"Invalid operation version for '{op}'") from exc
    provider_map = f"{domain}.{subdomain}.{name}"
    provider_queries = _get_provider_queries()
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
    return response.to_result()
