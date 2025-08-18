# providers/mssql_provider/__init__.py
from typing import Any, Dict
from .logic import init_pool, close_pool, fetch_json_one, fetch_json_many, fetch_row_one, exec_
from .registry import get_handler

async def init(**cfg):
    # pass: dsn="...", etc.
    await init_pool(**cfg)

async def dispatch(op: str, args: Dict[str, Any]):
    handler = get_handler(op)
    spec = handler(args)
    # async handler path
    if hasattr(spec, "__await__"):
        return await spec  # expected {"rows":[...], "rowcount":N}
    # tuple path: (mode, sql, params)
    mode, sql, params = spec
    if mode == "json_one":
        row = await fetch_json_one(sql, params)
        return {"rows": [row] if row else [], "rowcount": 1 if row else 0}
    if mode == "row_one":
        row = await fetch_row_one(sql, params)
        return {"rows": [row] if row else [], "rowcount": 1 if row else 0}
    if mode == "json_many":
        rows = await fetch_json_many(sql, params)
        return {"rows": rows, "rowcount": len(rows)}
    if mode == "exec":
        rc = await exec_(sql, params)
        return {"rows": [], "rowcount": rc}
    raise ValueError(f"Unknown mode: {mode}")
