# providers/database/mssql_provider/__init__.py
import logging
from typing import Any, Callable, Mapping

from ... import DbProviderBase
from server.registry import get_handler as resolve_handler, parse_db_op
from server.registry.types import DBRequest, DBResponse
from .logic import init_pool, close_pool

def get_handler(op: str):
  return resolve_handler(op, provider="mssql")


logger = logging.getLogger(__name__)


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  async def _run(self, request: DBRequest) -> DBResponse:
    self.log_dispatch(request.op)
    handler = self.resolve_handler(request.op)
    result = await self.call_handler(handler, request.payload)
    return self.normalize_response(request.op, result)

  def resolve_handler(self, op: str) -> Callable[[Mapping[str, Any]], Any]:
    return get_handler(op)

  def describe_operation(self, op: str) -> tuple[str, tuple[str, ...], int]:
    return parse_db_op(op)

  def log_dispatch(self, op: str) -> None:
    domain, path, version = self.describe_operation(op)
    logger.debug(
      "[%s] dispatching op=%s domain=%s path=%s v=%d",
      self.__class__.__name__,
      op,
      domain,
      "/".join(path),
      version,
    )

  async def call_handler(
    self,
    handler: Callable[[Mapping[str, Any]], Any],
    payload: Mapping[str, Any],
  ) -> Any:
    return await self.await_handler_result(handler(payload))

  async def await_handler_result(self, result: Any) -> Any:
    if hasattr(result, "__await__"):
      return await result
    return result

  def normalize_response(self, op: str, result: Any) -> DBResponse:
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

