# providers/database/mssql_provider/__init__.py
import logging
from typing import Any, Dict

from ... import DbProviderBase, DbRunMode
from server.registry import get_handler as resolve_handler, parse_db_op
from server.registry.types import DBRequest, DBResponse
from .logic import init_pool, close_pool
from .db_helpers import fetch_rows, fetch_json, exec_query

def get_handler(op: str):
  return resolve_handler(op, provider="mssql")


logger = logging.getLogger(__name__)


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  async def _run(self, request: DBRequest) -> DBResponse:
    domain, path, version = parse_db_op(request.op)
    logger.debug(
      "[MssqlProvider] dispatching op=%s domain=%s path=%s v=%d",
      request.op,
      domain,
      "/".join(path),
      version,
    )
    handler = get_handler(request.op)
    spec = handler(request.payload)
    result = await self._execute_spec(spec)
    return self._normalize_response(request.op, result)

  async def _execute_spec(self, spec: Any) -> Any:
    if hasattr(spec, "__await__"):
      return await spec
    if isinstance(spec, tuple) and len(spec) == 3:
      mode, sql, params = spec
      if mode is DbRunMode.JSON_ONE:
        return await fetch_json(sql, params)
      if mode is DbRunMode.ROW_ONE:
        return await fetch_rows(sql, params, one=True)
      if mode is DbRunMode.ROW_MANY:
        return await fetch_rows(sql, params)
      if mode is DbRunMode.JSON_MANY:
        return await fetch_json(sql, params, many=True)
      if mode is DbRunMode.EXEC:
        return await exec_query(sql, params)
      raise ValueError(f"Unknown mode: {mode}")
    return spec

  def _normalize_response(self, op: str, result: Any) -> DBResponse:
    if isinstance(result, DBResponse):
      if not result.op:
        result.attach_op(op)
      return result
    if isinstance(result, dict):
      rows = result.get("rows")
      rowcount = result.get("rowcount")
      payload = result.get("payload", rows)
      return DBResponse(op=op, payload=payload, rowcount=rowcount)
    if result is None:
      return DBResponse(op=op, payload=[], rowcount=0)
    raise TypeError(f"Unexpected MSSQL handler result type: {type(result)!r}")

