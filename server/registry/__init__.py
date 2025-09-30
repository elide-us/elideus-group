"""Registry dispatcher bridge."""

from __future__ import annotations

from typing import Awaitable, Callable

from server.modules.providers import DBResult, DbProviderBase

from .types import DBRequest, DBResponse

__all__ = [
  "DBRequest",
  "DBResponse",
  "DBResult",
  "RegistryDispatcher",
]


Executor = Callable[[DBRequest], Awaitable[DBResponse]]


def _current_dbresult_cls():
  from server.modules.providers import DBResult as ProvidersDBResult
  return ProvidersDBResult


class RegistryDispatcher:
  """Simple dispatcher that routes :class:`DBRequest` objects."""

  def __init__(self):
    self._executor: Executor | None = None

  def set_executor(self, executor: Executor) -> None:
    self._executor = executor

  def bind_provider(self, provider: DbProviderBase) -> None:
    async def _execute(request: DBRequest) -> DBResponse:
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
    return await self._executor(request)
