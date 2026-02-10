# providers/database/mssql_provider/__init__.py
import logging
from typing import Any
from queryregistry.helpers import parse_query_operation
from queryregistry.models import DBRequest, DBResponse

from ... import DbProviderBase
from .logic import init_pool, close_pool


logger = logging.getLogger(__name__)


class MssqlProvider(DbProviderBase):
  provider = "mssql"

  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  async def _run(self, request: DBRequest) -> DBResponse:
    self.log_dispatch(request.op)
    from queryregistry.handler import dispatch_query_request

    response = await dispatch_query_request(request, provider=self.provider)
    return self.normalize_response(request.op, response)

  def describe_operation(self, op: str) -> tuple[str, tuple[str, ...], int]:
    domain, remainder = parse_query_operation(op)
    if len(remainder) < 2:
      raise ValueError(f"Invalid query operation: {op}")
    *path, version_str = remainder
    try:
      version = int(version_str)
    except ValueError as exc:
      raise ValueError(f"Invalid query operation version: {op}") from exc
    return domain, tuple(path), version

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
