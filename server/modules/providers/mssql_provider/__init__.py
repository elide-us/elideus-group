# providers/mssql_provider/__init__.py
from typing import Any, Dict

from .. import DbProviderBase
from ..models import DBResult
from .logic import init_pool, close_pool
from .db_helpers import fetch_rows, fetch_json, exec_query
from .registry import get_handler


class MssqlProvider(DbProviderBase):
  async def startup(self) -> None:
    await init_pool(**self.config)

  async def shutdown(self) -> None:
    await close_pool()

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    handler = get_handler(op)
    spec = handler(args)
    if hasattr(spec, "__await__"):
      return await spec
    mode, sql, params = spec
    if mode == "json_one":
      return await fetch_json(sql, params)
    if mode == "row_one":
      return await fetch_rows(sql, params, one=True)
    if mode == "json_many":
      return await fetch_json(sql, params, many=True)
    if mode == "exec":
      return await exec_query(sql, params)
    raise ValueError(f"Unknown mode: {mode}")

