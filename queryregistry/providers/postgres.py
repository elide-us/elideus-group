"""Stubbed Postgres query registry provider helpers."""

from __future__ import annotations

from typing import Any, Iterable, Tuple


async def run_exec(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> Any:
  raise NotImplementedError("Postgres query execution is not implemented.")


async def run_json_one(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> Any:
  raise NotImplementedError("Postgres JSON query execution is not implemented.")


async def run_json_many(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> Any:
  raise NotImplementedError("Postgres JSON query execution is not implemented.")


async def run_rows_one(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> Any:
  raise NotImplementedError("Postgres row query execution is not implemented.")


async def run_rows_many(sql: str, params: Iterable[Any] | Tuple[Any, ...] = ()) -> Any:
  raise NotImplementedError("Postgres row query execution is not implemented.")
