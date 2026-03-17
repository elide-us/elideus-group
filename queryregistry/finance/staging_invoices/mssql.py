from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one


async def insert_invoice_batch_v1(args: Mapping[str, Any]) -> DBResponse:
  rows = args.get("rows") or []
  inserted = 0
  sql = """
    SET NOCOUNT ON;
    INSERT INTO finance_staging_azure_invoices (
      imports_recid,
      element_invoice_name,
      element_invoice_date,
      element_invoice_period_start,
      element_invoice_period_end,
      element_due_date,
      element_invoice_type,
      element_status,
      element_billed_amount,
      element_amount_due,
      element_currency,
      element_subscription_id,
      element_subscription_name,
      element_purchase_order,
      element_raw_json,
      element_created_on,
      element_modified_on
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME());
  """

  for row in rows:
    await run_exec(
      sql,
      (
        args["imports_recid"],
        row.get("element_invoice_name"),
        row.get("element_invoice_date"),
        row.get("element_invoice_period_start"),
        row.get("element_invoice_period_end"),
        row.get("element_due_date"),
        row.get("element_invoice_type"),
        row.get("element_status"),
        row.get("element_billed_amount"),
        row.get("element_amount_due"),
        row.get("element_currency"),
        row.get("element_subscription_id"),
        row.get("element_subscription_name"),
        row.get("element_purchase_order"),
        row.get("element_raw_json"),
      ),
    )
    inserted += 1

  return DBResponse(rows=[], rowcount=inserted)


async def list_invoices_by_import_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      imports_recid,
      element_invoice_name,
      element_invoice_date,
      element_invoice_period_start,
      element_invoice_period_end,
      element_due_date,
      element_invoice_type,
      element_status,
      element_billed_amount,
      element_amount_due,
      element_currency,
      element_subscription_id,
      element_subscription_name,
      element_purchase_order,
      element_raw_json,
      element_created_on,
      element_modified_on
    FROM finance_staging_azure_invoices
    WHERE imports_recid = ?
    ORDER BY element_invoice_date, recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["imports_recid"],))


async def get_invoice_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      imports_recid,
      element_invoice_name,
      element_invoice_date,
      element_invoice_period_start,
      element_invoice_period_end,
      element_due_date,
      element_invoice_type,
      element_status,
      element_billed_amount,
      element_amount_due,
      element_currency,
      element_subscription_id,
      element_subscription_name,
      element_purchase_order,
      element_raw_json,
      element_created_on,
      element_modified_on
    FROM finance_staging_azure_invoices
    WHERE element_invoice_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["invoice_name"],))


async def delete_invoices_by_import_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_staging_azure_invoices WHERE imports_recid = ?;
  """
  return await run_exec(sql, (args["imports_recid"],))
