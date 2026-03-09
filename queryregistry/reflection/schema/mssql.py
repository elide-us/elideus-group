"""MSSQL implementations for reflection schema query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many

__all__ = [
  "get_full_schema_v1",
  "list_columns_v1",
  "list_foreign_keys_v1",
  "list_indexes_v1",
  "list_tables_v1",
  "list_views_v1",
]


async def list_tables_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT recid, element_schema, element_name
    FROM system_schema_tables
    ORDER BY element_schema, element_name
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def list_columns_v1(args: Mapping[str, Any]) -> DBResponse:
  schema_name = args["schema"]
  table_name = args["name"]
  sql = """
    SELECT c.tables_recid, c.element_name, c.element_nullable, c.element_default,
           c.element_max_length, c.element_is_primary_key, c.element_is_identity,
           c.element_ordinal, m.element_mssql_type
    FROM system_schema_columns c
    JOIN system_edt_mappings m ON c.edt_recid = m.recid
    JOIN system_schema_tables t ON c.tables_recid = t.recid
    WHERE t.element_schema = ? AND t.element_name = ?
    ORDER BY c.element_ordinal
    FOR JSON PATH;
  """
  return await run_json_many(sql, (schema_name, table_name))


async def list_indexes_v1(args: Mapping[str, Any]) -> DBResponse:
  schema_name = args["schema"]
  table_name = args["name"]
  sql = """
    SELECT i.tables_recid, i.element_name, i.element_columns, i.element_is_unique
    FROM system_schema_indexes i
    JOIN system_schema_tables t ON i.tables_recid = t.recid
    WHERE t.element_schema = ? AND t.element_name = ?
    ORDER BY i.element_name
    FOR JSON PATH;
  """
  return await run_json_many(sql, (schema_name, table_name))


async def list_foreign_keys_v1(args: Mapping[str, Any]) -> DBResponse:
  schema_name = args["schema"]
  table_name = args["name"]
  sql = """
    SELECT fk.tables_recid, fk.element_column_name, fk.referenced_tables_recid,
           fk.element_referenced_column
    FROM system_schema_foreign_keys fk
    JOIN system_schema_tables t ON fk.tables_recid = t.recid
    WHERE t.element_schema = ? AND t.element_name = ?
    ORDER BY fk.element_column_name
    FOR JSON PATH;
  """
  return await run_json_many(sql, (schema_name, table_name))


async def list_views_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT element_schema, element_name, element_definition
    FROM system_schema_views
    ORDER BY element_schema, element_name
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_full_schema_v1(_: Mapping[str, Any]) -> DBResponse:
  tables = await run_json_many(
    """
    SELECT recid, element_schema, element_name
    FROM system_schema_tables
    ORDER BY element_schema, element_name
    FOR JSON PATH;
    """
  )
  columns = await run_json_many(
    """
    SELECT c.tables_recid, c.element_name, c.element_nullable, c.element_default,
           c.element_max_length, c.element_is_primary_key, c.element_is_identity,
           c.element_ordinal, m.element_mssql_type
    FROM system_schema_columns c
    JOIN system_edt_mappings m ON c.edt_recid = m.recid
    ORDER BY c.tables_recid, c.element_ordinal
    FOR JSON PATH;
    """
  )
  indexes = await run_json_many(
    """
    SELECT i.tables_recid, i.element_name, i.element_columns, i.element_is_unique
    FROM system_schema_indexes i
    ORDER BY i.tables_recid, i.element_name
    FOR JSON PATH;
    """
  )
  foreign_keys = await run_json_many(
    """
    SELECT fk.tables_recid, fk.element_column_name, fk.referenced_tables_recid,
           fk.element_referenced_column
    FROM system_schema_foreign_keys fk
    ORDER BY fk.tables_recid, fk.element_column_name
    FOR JSON PATH;
    """
  )
  views = await run_json_many(
    """
    SELECT element_schema, element_name, element_definition
    FROM system_schema_views
    ORDER BY element_schema, element_name
    FOR JSON PATH;
    """
  )
  payload = {
    "tables": tables.payload,
    "columns": columns.payload,
    "indexes": indexes.payload,
    "foreign_keys": foreign_keys.payload,
    "views": views.payload,
  }
  return DBResponse(payload=payload, rowcount=len(payload["tables"]))
