# providers/postgres_provider/__init__.py
from typing import Any, Dict
from .logic import init_pool, close_pool, fetch_one, fetch_many, execute
from .registry import get_handler

async def init(**cfg):
  await init_pool(**cfg)

async def dispatch(op: str, args: Dict[str, Any]):
  handler = get_handler(op)
  spec = handler(args)
  if hasattr(spec, '__await__'):
    return await spec
  mode, sql, params = spec
  if mode == 'one':
    row = await fetch_one(sql, params)
    return {"rows": [row] if row else [], "rowcount": 1 if row else 0}
  if mode == 'many':
    rows = await fetch_many(sql, params)
    return {"rows": rows, "rowcount": len(rows)}
  if mode == 'exec':
    rc = await execute(sql, params)
    return {"rows": [], "rowcount": rc}
  raise ValueError(f"Unknown mode: {mode}")

