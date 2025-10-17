"""Utility wrappers for executing MSSQL registry operations."""

from __future__ import annotations

from typing import Any, Iterable, Tuple

from server.modules.providers.database.mssql_provider.db_helpers import exec_query, fetch_json, fetch_rows
from server.registry.types import DBResponse

__all__ = [
  "run_exec",
  "run_json_many",
  "run_json_one",
  "run_rows_many",
  "run_rows_one",
]


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
