import json, logging
from typing import Any, Iterable, AsyncIterator
from . import logic
from ... import DBResponse

def _rowdict(cols: Iterable[str], row: Iterable[Any]):
  return dict(zip(cols, row))

async def fetch_rows(query: str, params: tuple[Any, ...] = (), *, one: bool = False, stream: bool = False) -> DBResponse | AsyncIterator[dict]:
  assert logic._pool, "MSSQL pool not initialized"
  async def _ensure_result_set(cur) -> bool:
    if cur.description is not None:
      return True
    while await cur.nextset():
      if cur.description is not None:
        return True
    return False
  if stream:
    async def _stream() -> AsyncIterator[dict]:
      try:
        async with logic._pool.acquire() as conn:
          async with conn.cursor() as cur:
            await cur.execute(query, params)
            if not await _ensure_result_set(cur):
              return
            cols = [c[0] for c in cur.description]
            while True:
              row = await cur.fetchone()
              if not row:
                break
              yield _rowdict(cols, row)
      except Exception as e:
        logging.debug(f"Stream failed:\n{query}\nArgs: {params}\nError: {e}")
    return _stream()
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        if not await _ensure_result_set(cur):
          return DBResponse()
        cols = [c[0] for c in cur.description]
        if one:
          row = await cur.fetchone()
          if not row:
            return DBResponse()
          return DBResponse(rows=[_rowdict(cols, row)], rowcount=1)
        rows_raw = await cur.fetchall()
        rows = [_rowdict(cols, r) for r in rows_raw]
        return DBResponse(rows=rows, rowcount=len(rows))
  except Exception as e:
    logging.debug(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    return DBResponse()

async def fetch_json(query: str, params: tuple[Any, ...] = (), *, many: bool = False) -> DBResponse:
  assert logic._pool, "MSSQL pool not initialized"
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        parts: list[str] = []
        while True:
          row = await cur.fetchone()
          if not row or not row[0]:
            break
          parts.append(row[0])
        if not parts:
          return DBResponse()
        data = json.loads("".join(parts))
        if many and isinstance(data, list):
          return DBResponse(rows=data, rowcount=len(data))
        return DBResponse(rows=[data], rowcount=1)
  except Exception as e:
    logging.error(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    raise

async def exec_query(query: str, params: tuple[Any, ...] = ()) -> DBResponse:
  assert logic._pool, "MSSQL pool not initialized"
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        return DBResponse(rowcount=cur.rowcount or 0)
  except Exception as e:
    logging.error(f"Exec failed:\n{query}\nArgs: {params}\nError: {e}")
    raise
