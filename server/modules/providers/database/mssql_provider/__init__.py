# providers/database/mssql_provider/__init__.py
import inspect
from typing import Any, Dict

from ... import DbProviderBase, DBResult
from .logic import init_pool, close_pool
from .db_helpers import Operation, execute_operation
from .registry import get_handler


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    handler = get_handler(op)
    spec = handler(args)
    if inspect.isawaitable(spec):
      result = await spec  # type: ignore[func-returns-value]
      if isinstance(result, DBResult):
        return result
      raise TypeError(f"Handler '{op}' returned unexpected awaitable result: {type(result)!r}")
    if isinstance(spec, Operation):
      return await execute_operation(spec)
    raise TypeError(f"Handler '{op}' returned unsupported spec type: {type(spec)!r}")

