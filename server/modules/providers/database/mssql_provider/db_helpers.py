import json, logging
from typing import Any, Iterable, AsyncIterator
from . import logic
from ... import DBResponse

def _rowdict(cols: Iterable[str], row: Iterable[Any]):
  return dict(zip(cols, row))

async def fetch_rows(query: str, params: tuple[Any, ...] = (), *, one: bool = False, stream: bool = False) -> DBResponse | AsyncIterator[dict]:
  params = params or ()
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
  params = params or ()
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
        raw = "".join(parts)
        try:
          data = json.loads(raw)
        except json.JSONDecodeError:
          # WITHOUT_ARRAY_WRAPPER with multiple rows produces concatenated
          # JSON objects: {"a":1}{"a":2}. Wrap in array brackets to parse.
          try:
            # Insert commas between adjacent }{ boundaries
            import re
            wrapped = "[" + re.sub(r'\}\s*\{', '},{', raw) + "]"
            data = json.loads(wrapped)
            logging.warning(
              "fetch_json recovered concatenated JSON objects (%d items). "
              "Consider adding TOP 1 to the query or removing WITHOUT_ARRAY_WRAPPER.",
              len(data) if isinstance(data, list) else 1,
            )
          except json.JSONDecodeError:
            logging.error(f"[JSONDecodeError] fetch_json — unparseable JSON:\n{raw[:500]}")
            raise
        if many and isinstance(data, list):
          return DBResponse(rows=data, rowcount=len(data))
        if isinstance(data, list):
          # many=False but got a list (recovered from concatenation) — return first
          return DBResponse(rows=[data[0]] if data else [], rowcount=1)
        return DBResponse(rows=[data], rowcount=1)
  except Exception as e:
    logging.error(f"Query failed:\n{query}\nArgs: {params}\nError: {e}")
    raise

async def exec_query(query: str, params: tuple[Any, ...] = ()) -> DBResponse:
  params = params or ()
  assert logic._pool, "MSSQL pool not initialized"
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        return DBResponse(rowcount=cur.rowcount or 0)
  except Exception as e:
    logging.error(f"Exec failed:\n{query}\nArgs: {params}\nError: {e}")
    raise
