import json, logging
from dataclasses import dataclass
from typing import Any, Iterable, AsyncIterator, Awaitable, Callable, Dict
from . import logic
from ... import DBResult, DbRunMode


@dataclass(slots=True)
class Operation:
  kind: DbRunMode
  sql: str
  params: tuple[Any, ...] = ()
  postprocess: Callable[[DBResult], DBResult] | None = None

  def __post_init__(self):
    if not isinstance(self.params, tuple):
      object.__setattr__(self, "params", tuple(self.params))

  def __iter__(self):
    yield self.kind
    yield self.sql
    yield self.params


def row_one(sql: str, params: Iterable[Any] = (), *, postprocess: Callable[[DBResult], DBResult] | None = None) -> Operation:
  return Operation(DbRunMode.ROW_ONE, sql, tuple(params), postprocess)


def row_many(sql: str, params: Iterable[Any] = (), *, postprocess: Callable[[DBResult], DBResult] | None = None) -> Operation:
  return Operation(DbRunMode.ROW_MANY, sql, tuple(params), postprocess)


def json_one(sql: str, params: Iterable[Any] = (), *, postprocess: Callable[[DBResult], DBResult] | None = None) -> Operation:
  return Operation(DbRunMode.JSON_ONE, sql, tuple(params), postprocess)


def json_many(sql: str, params: Iterable[Any] = (), *, postprocess: Callable[[DBResult], DBResult] | None = None) -> Operation:
  return Operation(DbRunMode.JSON_MANY, sql, tuple(params), postprocess)


def exec_op(sql: str, params: Iterable[Any] = (), *, postprocess: Callable[[DBResult], DBResult] | None = None) -> Operation:
  return Operation(DbRunMode.EXEC, sql, tuple(params), postprocess)


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

async def fetch_rows(operation: Operation, *, stream: bool = False) -> DBResult | AsyncIterator[dict]:
  assert logic._pool, "MSSQL pool not initialized"
  if operation.kind not in (DbRunMode.ROW_ONE, DbRunMode.ROW_MANY):
    raise ValueError(f"Operation kind '{operation.kind}' is not row fetch capable")
  query = operation.sql
  params = operation.params
  one = operation.kind is DbRunMode.ROW_ONE
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

async def fetch_json(operation: Operation) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  if operation.kind not in (DbRunMode.JSON_ONE, DbRunMode.JSON_MANY):
    raise ValueError(f"Operation kind '{operation.kind}' is not JSON fetch capable")
  query = operation.sql
  params = operation.params
  many = operation.kind is DbRunMode.JSON_MANY
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

async def exec_query(operation: Operation) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  if operation.kind is not DbRunMode.EXEC:
    raise ValueError(f"Operation kind '{operation.kind}' is not executable")
  query = operation.sql
  params = operation.params
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        return DBResult(rowcount=cur.rowcount or 0)
  except Exception as e:
    _raise_query_error(query, params, e, log=logging.error)


_RUNNERS: Dict[DbRunMode, Callable[[Operation], Awaitable[DBResult]]] = {
  DbRunMode.ROW_ONE: fetch_rows,
  DbRunMode.ROW_MANY: fetch_rows,
  DbRunMode.JSON_ONE: fetch_json,
  DbRunMode.JSON_MANY: fetch_json,
  DbRunMode.EXEC: exec_query,
}


async def execute_operation(operation: Operation) -> DBResult:
  try:
    runner = _RUNNERS[operation.kind]
  except KeyError:
    raise ValueError(f"Unknown operation kind: {operation.kind}") from None
  result = await runner(operation)
  if operation.postprocess:
    return operation.postprocess(result)
  return result
