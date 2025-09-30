# providers/database/mssql_provider/__init__.py
import inspect
from typing import Any, Dict
from collections.abc import Mapping

from pydantic import ValidationError

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
      spec = await spec  # type: ignore[func-returns-value]

    async def _resolve(result: Any) -> DBResult:
      if isinstance(result, Operation):
        return await execute_operation(result)
      if isinstance(result, DBResult):
        return result
      if isinstance(result, Mapping):
        validator = getattr(DBResult, "model_validate", None)
        try:
          if callable(validator):
            return validator(result)
          return DBResult(**result)
        except (ValidationError, TypeError, ValueError) as exc:
          raise TypeError(
            f"Handler '{op}' returned mapping that cannot be parsed as DBResult"
          ) from exc
      raise TypeError(
        f"Handler '{op}' returned unsupported result type: {type(result)!r}."
        " Expected Operation, DBResult, or mapping with rows/rowcount."
      )

    return await _resolve(spec)

