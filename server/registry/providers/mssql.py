"""Utility wrappers for executing MSSQL registry operations."""

from __future__ import annotations

from typing import Any, Iterable, Protocol, Tuple

from server.modules.providers.database.mssql_provider.db_helpers import (
  exec_query,
  fetch_json,
  fetch_rows,
)
from server.modules.providers.database.mssql_provider.logic import transaction
from server.registry.types import DBResponse

__all__ = [
  "configure",
  "run_exec",
  "run_json_many",
  "run_json_one",
  "run_rows_many",
  "run_rows_one",
  "transaction",
]


class _EnvReader(Protocol):
  def get(self, key: str) -> str | None: ...


def configure(env: _EnvReader) -> dict[str, Any]:
  """Return configuration used to initialize the MSSQL provider."""

  dsn = env.get("AZURE_SQL_CONNECTION_STRING")
  if not dsn:
    raise RuntimeError("AZURE_SQL_CONNECTION_STRING must be configured for MSSQL provider")
  return {"dsn": dsn}


async def run_exec(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> DBResponse:
  return await exec_query(sql, tuple(params))


async def run_json_one(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> DBResponse:
  return await fetch_json(sql, tuple(params), many=False)


async def run_json_many(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> DBResponse:
  return await fetch_json(sql, tuple(params), many=True)


async def run_rows_one(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> DBResponse:
  return await fetch_rows(sql, tuple(params), one=True)


async def run_rows_many(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> DBResponse:
  return await fetch_rows(sql, tuple(params), one=False)
