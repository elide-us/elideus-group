import json, logging
from dataclasses import dataclass
from typing import Any, Iterable, AsyncIterator, Callable
from . import logic
from ... import DBResult


@dataclass(slots=True)
class QueryErrorDetail:
  query: str
  params: tuple[Any, ...]
  message: str


class DBQueryError(RuntimeError):
  def __init__(self, detail: QueryErrorDetail, *, original: Exception | None = None):
    super().__init__(detail.message)
    self.detail = detail
    self.original = original


def _raise_query_error(query: str, params: tuple[Any, ...], error: Exception, *, log: Callable[[str], Any]):
  log(f"Query failed:\n{query}\nArgs: {params}\nError: {error}")
  detail = QueryErrorDetail(query=query, params=params, message=str(error))
  raise DBQueryError(detail, original=error) from error

def _rowdict(cols: Iterable[str], row: Iterable[Any]):
  return dict(zip(cols, row))

async def fetch_rows(query: str, params: tuple[Any, ...] = (), *, one: bool = False, stream: bool = False) -> DBResult | AsyncIterator[dict]:
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
        _raise_query_error(query, params, e, log=logging.debug)
    return _stream()
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        if not await _ensure_result_set(cur):
          return DBResult()
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
    _raise_query_error(query, params, e, log=logging.debug)

async def fetch_json(query: str, params: tuple[Any, ...] = (), *, many: bool = False) -> DBResult:
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
          return DBResult()
        data = json.loads("".join(parts))
        if data is None:
          return DBResult()
        if many:
          if isinstance(data, list):
            return DBResult(rows=data, rowcount=len(data))
          return DBResult(rows=[data], rowcount=1)
        if isinstance(data, list):
          return DBResult(rows=data, rowcount=len(data))
        return DBResult(rows=[data], rowcount=1)
  except Exception as e:
    _raise_query_error(query, params, e, log=logging.error)

async def exec_query(query: str, params: tuple[Any, ...] = ()) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        return DBResult(rowcount=cur.rowcount or 0)
  except Exception as e:
    _raise_query_error(query, params, e, log=logging.error)
