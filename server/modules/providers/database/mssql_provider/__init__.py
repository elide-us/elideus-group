# providers/database/mssql_provider/__init__.py
from typing import Any, Dict
from collections.abc import Mapping
import inspect
import importlib

from pydantic import ValidationError

from ... import DbProviderBase, DBResult
from .logic import init_pool, close_pool
from .db_helpers import Operation, execute_operation
from . import registry as registry

get_handler = registry.get_handler
from server.registry.providers.mssql import PROVIDER_QUERIES
from server.registry.types import DBRequest, DBResponse


def _current_dbresult_cls():
  providers_mod = importlib.import_module("server.modules.providers")
  return getattr(providers_mod, "DBResult")


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  def _resolve_provider_callable(self, op: str):
    try:
      handler = get_handler(op)
    except KeyError:
      parts = op.split(":")
      if len(parts) != 5 or parts[0] != "db":
        raise KeyError(f"Unsupported operation key: {op}")
      _, domain, subdomain, name, version_str = parts
      try:
        version = int(version_str)
      except ValueError as exc:
        raise KeyError(f"Invalid operation version for '{op}'") from exc
      provider_map = f"{domain}.{subdomain}.{name}"
      entry = PROVIDER_QUERIES.get(provider_map)
      if entry is None:
        raise KeyError(f"No MSSQL handler for '{op}'")
      if isinstance(entry, Mapping):
        handler = entry.get(version)
      else:
        handler = entry
      if handler is None:
        raise KeyError(f"No MSSQL handler for '{op}' version {version}")
      return handler
    expects_dbrequest = False
    try:
      signature = inspect.signature(handler)
    except (TypeError, ValueError):
      signature = None
    if signature:
      params = list(signature.parameters.values())
      if params and params[0].annotation is DBRequest:
        expects_dbrequest = True

    if expects_dbrequest:
      return handler

    async def _wrapped(request: DBRequest):
      call_arg: Any = request.params
      result = handler(call_arg)
      if inspect.isawaitable(result):
        result = await result
      return result

    return _wrapped

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    handler = self._resolve_provider_callable(op)
    request = DBRequest(op=op, params=args)
    spec = await handler(request)

    if isinstance(spec, DBResponse):
      return spec.to_result()

    DBResultCls = _current_dbresult_cls()

    async def _resolve(result: Any) -> DBResult:
      if isinstance(result, Operation):
        return await execute_operation(result)
      if isinstance(result, DBResultCls):
        return result
      if isinstance(result, Mapping):
        validator = getattr(DBResultCls, "model_validate", None)
        try:
          if callable(validator):
            return validator(result)
          return DBResultCls(**result)
        except (ValidationError, TypeError, ValueError) as exc:
          raise TypeError(
            f"Handler '{op}' returned mapping that cannot be parsed as DBResult"
          ) from exc
      raise TypeError(
        f"Handler '{op}' returned unsupported result type: {type(result)!r}."
        " Expected Operation, DBResult, mapping, or DBResponse."
      )

    return await _resolve(spec)
