"""MSSQL implementations for reflection data query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from .models import QueryInfoSchemaParams

__all__ = [
  "apply_batch_v1",
  "dump_table_v1",
  "get_version_v1",
  "rebuild_indexes_v1",
  "update_version_v1",
  "query_info_schema_v1",
]


def _quote_ident(identifier: str) -> str:
  return "[" + identifier.replace("]", "]]" ) + "]"


async def get_version_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT element_value
    FROM system_config
    WHERE element_key='Version'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql)


async def update_version_v1(args: Mapping[str, Any]) -> DBResponse:
  version = args["version"]
  sql = "UPDATE system_config SET element_value=? WHERE element_key='Version';"
  return await run_exec(sql, (version,))


async def dump_table_v1(args: Mapping[str, Any]) -> DBResponse:
  schema_name = _quote_ident(args["table_schema"])
  table_name = _quote_ident(args["name"])
  sql = f"SELECT * FROM {schema_name}.{table_name} FOR JSON PATH;"
  return await run_json_many(sql)


async def rebuild_indexes_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = "EXEC sp_MSforeachtable 'ALTER INDEX ALL ON ? REBUILD'"
  return await run_exec(sql)


async def apply_batch_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = args["sql"]
  return await run_exec(sql)


async def query_info_schema_v1(args: Mapping[str, Any]) -> DBResponse:
  params = QueryInfoSchemaParams.model_validate(args)
  ident = _quote_ident(params.view_name)
  sql = f"SELECT * FROM INFORMATION_SCHEMA.{ident}"
  query_params: tuple[str, ...] = ()
  if params.filter_column is not None and params.filter_value is not None:
    col_ident = _quote_ident(params.filter_column)
    sql += f" WHERE {col_ident} = ?"
    query_params = (params.filter_value,)
  sql += " FOR JSON PATH;"
  return await run_json_many(sql, query_params)
