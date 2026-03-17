from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many


async def insert_line_items_batch_v1(args: Mapping[str, Any]) -> DBResponse:
  rows = args.get("rows") or []
  inserted = 0
  sql = """
    INSERT INTO finance_staging_line_items (
      imports_recid,
      vendors_recid,
      element_date,
      element_service,
      element_category,
      element_description,
      element_quantity,
      element_unit_price,
      element_amount,
      element_currency,
      element_raw_json,
      element_created_on
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME());
  """
  for row in rows:
    await run_exec(
      sql,
      (
        args["imports_recid"],
        args["vendors_recid"],
        row.get("element_date"),
        row.get("element_service"),
        row.get("element_category"),
        row.get("element_description"),
        row.get("element_quantity"),
        row.get("element_unit_price"),
        row.get("element_amount") or 0,
        row.get("element_currency"),
        row.get("element_raw_json"),
      ),
    )
    inserted += 1
  return DBResponse(rows=[], rowcount=inserted)


async def list_line_items_by_import_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      line.recid,
      line.imports_recid,
      line.vendors_recid,
      vendor.element_name AS vendor_name,
      line.element_date,
      line.element_service,
      line.element_category,
      line.element_description,
      line.element_quantity,
      line.element_unit_price,
      line.element_amount,
      line.element_currency,
      line.element_raw_json,
      line.element_created_on
    FROM finance_staging_line_items AS line
    INNER JOIN finance_vendors AS vendor
      ON vendor.recid = line.vendors_recid
    WHERE line.imports_recid = ?
    ORDER BY line.recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["imports_recid"],))


async def aggregate_line_items_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      element_service,
      element_category,
      element_record_type,
      SUM(element_amount) AS element_total_amount,
      COUNT_BIG(1) AS element_row_count
    FROM finance_staging_line_items
    WHERE imports_recid = ?
    GROUP BY element_service, element_category, element_record_type
    ORDER BY element_record_type, element_service, element_category
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["imports_recid"],))


async def delete_line_items_by_import_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_staging_line_items
    WHERE imports_recid = ?;
  """
  return await run_exec(sql, (args["imports_recid"],))
