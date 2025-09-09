import json, logging
from typing import Any, Iterable, AsyncIterator
from . import logic
from ... import DBResult

def _rowdict(cols: Iterable[str], row: Iterable[Any]):
  return dict(zip(cols, row))

async def fetch_rows(query: str, params: tuple[Any, ...] = (), *, one: bool = False, stream: bool = False) -> DBResult | AsyncIterator[dict]:
  assert logic._pool, "MSSQL pool not initialized"
  if stream:
    async def _stream() -> AsyncIterator[dict]:
      try:
        async with logic._pool.acquire() as conn:
          async with conn.cursor() as cur:
            await cur.execute(query, params)
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
        cols = [c[0] for c in cur.description]
        if one:
          row = await cur.fetchone()
          if not row:
            return DBResult()
          return DBResult(rows=[_rowdict(cols, row)], rowcount=1)
        rows_raw = await cur.fetchall()
        rows = [_rowdict(cols, r) for r in rows_raw]
        return DBResult(rows=rows, rowcount=len(rows))
  except Exception as e:
    logging.debug(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    return DBResult()

async def fetch_json(query: str, params: tuple[Any, ...] = (), *, many: bool = False) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        row = await cur.fetchone()
        if not row or not row[0]:
          return DBResult()
        data = json.loads(row[0])
        if many and isinstance(data, list):
          return DBResult(rows=data, rowcount=len(data))
        return DBResult(rows=[data], rowcount=1)
  except Exception as e:
    logging.error(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    raise

async def exec_query(query: str, params: tuple[Any, ...] = ()) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        return DBResult(rowcount=cur.rowcount or 0)
  except Exception as e:
    logging.error(f"Exec failed:\n{query}\nArgs: {params}\nError: {e}")
    raise
