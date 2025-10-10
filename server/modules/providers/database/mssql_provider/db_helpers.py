import importlib
import json, logging
from dataclasses import dataclass
from typing import Any, Iterable, AsyncIterator, Callable
from . import logic
from ... import DBResult, DbRunMode
from server.helpers.context import get_request_id


def _current_run_mode():
  providers_mod = importlib.import_module("server.modules.providers")
  return getattr(providers_mod, "DbRunMode")


def _coerce_run_mode(kind: DbRunMode | str) -> DbRunMode:
  run_mode_cls = _current_run_mode()
  if isinstance(kind, run_mode_cls):
    return kind
  value = getattr(kind, "value", kind)
  try:
    return run_mode_cls(value)
  except Exception as exc:
    try:
      return run_mode_cls(str(value))
    except Exception as inner_exc:
      raise TypeError(f"Unsupported run mode value: {value!r}") from inner_exc


@dataclass(slots=True)
class QueryErrorDetail:
  query: str
  params: tuple[Any, ...]
  message: str
  request_id: str | None = None


class DBQueryError(RuntimeError):
  def __init__(self, detail: QueryErrorDetail, *, original: Exception | None = None):
    super().__init__(detail.message)
    self.detail = detail
    self.original = original


def _raise_query_error(query: str, params: tuple[Any, ...], error: Exception, *, log: Callable[[str], Any]):
  request_id = get_request_id()
  prefix = f"[MSSQL {request_id}] " if request_id else "[MSSQL] "
  log(f"{prefix}Query failed:\n{query}\nArgs: {params}\nError: {error}")
  detail = QueryErrorDetail(query=query, params=params, message=str(error), request_id=request_id)
  raise DBQueryError(detail, original=error) from error

def _rowdict(cols: Iterable[str], row: Iterable[Any]):
  return dict(zip(cols, row))

async def _ensure_result_set(cur) -> bool:
  if not hasattr(cur, "description"):
    return True
  if getattr(cur, "description", None) is not None:
    return True
  nextset = getattr(cur, "nextset", None)
  if not nextset:
    return False
  while await nextset():
    if getattr(cur, "description", None) is not None:
      return True
  return False

async def fetch_rows(kind: DbRunMode | str, sql: str, params: Iterable[Any] = (), *, stream: bool = False) -> DBResult | AsyncIterator[dict]:
  assert logic._pool, "MSSQL pool not initialized"
  run_mode_cls = _current_run_mode()
  mode = _coerce_run_mode(kind)
  if mode not in (run_mode_cls.ROW_ONE, run_mode_cls.ROW_MANY):
    raise ValueError(f"Operation kind '{mode}' is not row fetch capable")
  query = sql
  params = tuple(params)
  one = mode is run_mode_cls.ROW_ONE
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

async def fetch_json(kind: DbRunMode | str, sql: str, params: Iterable[Any] = ()) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  run_mode_cls = _current_run_mode()
  mode = _coerce_run_mode(kind)
  if mode not in (run_mode_cls.JSON_ONE, run_mode_cls.JSON_MANY):
    raise ValueError(f"Operation kind '{mode}' is not JSON fetch capable")
  query = sql
  params = tuple(params)
  many = mode is run_mode_cls.JSON_MANY
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        if not await _ensure_result_set(cur):
          return DBResult()
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

async def exec_query(sql: str, params: Iterable[Any] = ()) -> DBResult:
  assert logic._pool, "MSSQL pool not initialized"
  query = sql
  params = tuple(params)
  try:
    async with logic._pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(query, params)
        return DBResult(rowcount=cur.rowcount or 0)
  except Exception as e:
    _raise_query_error(query, params, e, log=logging.error)


async def run_operation(kind: DbRunMode | str, sql: str, params: Iterable[Any] = ()) -> DBResult:
  run_mode_cls = _current_run_mode()
  mode = _coerce_run_mode(kind)
  if mode in (run_mode_cls.ROW_ONE, run_mode_cls.ROW_MANY):
    return await fetch_rows(mode, sql, params)
  if mode in (run_mode_cls.JSON_ONE, run_mode_cls.JSON_MANY):
    return await fetch_json(mode, sql, params)
  if mode is run_mode_cls.EXEC:
    return await exec_query(sql, params)
  raise ValueError(f"Unknown operation kind: {mode}")
