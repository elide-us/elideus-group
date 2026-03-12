"""MSSQL implementations for finance staging query registry services."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "create_import_v1",
  "insert_cost_detail_batch_v1",
  "list_cost_details_by_import_v1",
  "list_imports_v1",
  "update_import_status_v1",
]

_VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _to_element_column_name(field_name: str) -> str:
  if not field_name:
    raise ValueError("Cost detail row contains an empty field name")
  if not _VALID_IDENTIFIER.fullmatch(field_name):
    raise ValueError(f"Cost detail field name contains unsupported characters: {field_name}")
  return f"element_{field_name}"


async def create_import_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    INSERT INTO finance_staging_imports (
      element_source,
      element_scope,
      element_metric,
      element_period_start,
      element_period_end,
      element_status,
      element_row_count,
      element_error,
      element_created_on,
      element_modified_on
    )
    OUTPUT inserted.*
    VALUES (?, ?, ?, ?, ?, 0, 0, NULL, SYSUTCDATETIME(), SYSUTCDATETIME());
  """
  params = (
    args["source"],
    args["scope"],
    args["metric"],
    args["period_start"],
    args["period_end"],
  )
  return await run_json_one(sql, params)


async def update_import_status_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    UPDATE finance_staging_imports
    SET
      element_status = ?,
      element_row_count = ?,
      element_error = ?,
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;
  """
  params = (args["status"], args["row_count"], args.get("error"), args["recid"])
  return await run_exec(sql, params)


async def insert_cost_detail_batch_v1(args: Mapping[str, Any]) -> DBResponse:
  imports_recid = args["imports_recid"]
  rows = args.get("rows") or []
  inserted = 0

  for row in rows:
    columns = ["imports_recid"]
    values: list[Any] = [imports_recid]

    for field_name, field_value in row.items():
      column_name = _to_element_column_name(field_name)
      columns.append(column_name)
      values.append(field_value)

    columns_sql = ", ".join(f"[{column}]" for column in columns)
    placeholders_sql = ", ".join("?" for _ in values)
    sql = f"""
      INSERT INTO finance_staging_cost_details ({columns_sql})
      VALUES ({placeholders_sql});
    """
    await run_exec(sql, tuple(values))
    inserted += 1

  return DBResponse(rows=[], rowcount=inserted)


async def list_imports_v1(args: Mapping[str, Any]) -> DBResponse:
  del args
  sql = """
    SELECT
      recid,
      element_source,
      element_scope,
      element_metric,
      element_period_start,
      element_period_end,
      element_status,
      element_row_count,
      element_error,
      element_created_on,
      element_modified_on
    FROM finance_staging_imports
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)


async def list_cost_details_by_import_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM finance_staging_cost_details
    WHERE imports_recid = ?
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["imports_recid"],))
