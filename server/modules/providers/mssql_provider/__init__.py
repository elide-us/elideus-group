# providers/mssql_provider/__init__.py
from typing import Any, Dict
from .logic import init_pool, close_pool
from .db_helpers import fetch_rows, fetch_json, exec_query
from .registry import get_handler

async def init(**cfg):
  # pass: dsn="...", etc.
  await init_pool(**cfg)

async def dispatch(op: str, args: Dict[str, Any]):
  handler = get_handler(op)
  spec = handler(args)
  # async handler path
  if hasattr(spec, "__await__"):
    return await spec
  # tuple path: (mode, sql, params)
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
