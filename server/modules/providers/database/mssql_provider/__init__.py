# providers/database/mssql_provider/__init__.py
from typing import Any, Dict
from collections.abc import Mapping
import inspect
import logging

from ... import DbProviderBase, DBResult
from .logic import init_pool, close_pool
from .db_helpers import run_operation

from importlib import import_module

from server.registry.types import DBRequest, DBResponse
from server.helpers.context import get_request_id
from server.errors import RPCServiceError, internal_error


_logger = logging.getLogger(__name__)


def _get_provider_queries():
  module = import_module("server.registry.providers.mssql")
  getter = getattr(module, "get_provider_queries", None)
  if callable(getter):
    return getter()
  return getattr(module, "PROVIDER_QUERIES")


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  def _resolve_provider_callable(self, op: str):
    provider_queries = _get_provider_queries()
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
    request_id = get_request_id()
    metadata = {'request_id': request_id} if request_id else None
    request = DBRequest(op=op, params=args, metadata=metadata)
    if request_id:
      _logger.debug('[MSSQL %s] Dispatching provider handler for %s', request_id, op)
    try:
      response = handler(request)
      if inspect.isawaitable(response):
        response = await response
    except RPCServiceError:
      raise
    except Exception as exc:
      _logger.error('[MSSQL %s] Handler failure for %s: %s', request_id, op, exc)
      raise internal_error(
        'Database provider execution failed',
        code='rpc.db.provider_failure',
        diagnostic=str(exc),
      ) from exc
    if not isinstance(response, DBResponse):
      raise TypeError(
        f"Handler '{op}' returned unsupported result type: {type(response)!r}."
        " Expected DBResponse."
      )
    if request_id:
      _logger.debug('[MSSQL %s] Provider handler completed for %s', request_id, op)
    return response.to_result(result_cls=DBResult)
