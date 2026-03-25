"""MSSQL implementations for system renewals query registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "delete_renewal_v1",
  "get_renewal_v1",
  "list_renewals_v1",
  "upsert_renewal_v1",
]


async def list_renewals_v1(args: Mapping[str, Any]) -> DBResponse:
  conditions = ["1=1"]
  params: list[Any] = []
  if args.get("category"):
    conditions.append("element_category = ?")
    params.append(args["category"])
  if args.get("status") is not None:
    conditions.append("element_status = ?")
    params.append(args["status"])
  where = " AND ".join(conditions)
  sql = f"""
    SELECT
      recid,
      element_guid,
      element_name,
      element_category,
      element_vendor,
      element_reference,
      element_expires_on,
      element_renew_by,
      element_renewal_cost,
      element_currency,
      element_auto_renew,
      element_owner,
      element_notes,
      element_status,
      element_created_on,
      element_modified_on
    FROM system_renewals
    WHERE {where}
    ORDER BY
      CASE WHEN element_expires_on IS NULL THEN 1 ELSE 0 END,
      element_expires_on ASC,
      element_name ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, tuple(params))


async def get_renewal_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      element_name,
      element_category,
      element_vendor,
      element_reference,
      element_expires_on,
      element_renew_by,
      element_renewal_cost,
      element_currency,
      element_auto_renew,
      element_owner,
      element_notes,
      element_status,
      element_created_on,
      element_modified_on
    FROM system_renewals
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def upsert_renewal_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    MERGE system_renewals AS target
    USING (SELECT ? AS recid) AS src ON target.recid = src.recid
    WHEN MATCHED THEN UPDATE SET
      element_name = ?,
      element_category = ?,
      element_vendor = ?,
      element_reference = ?,
      element_expires_on = TRY_CAST(? AS DATE),
      element_renew_by = TRY_CAST(? AS DATE),
      element_renewal_cost = TRY_CAST(? AS DECIMAL(19,5)),
      element_currency = ?,
      element_auto_renew = ?,
      element_owner = ?,
      element_notes = ?,
      element_status = ?,
      element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN INSERT (
      element_name,
      element_category,
      element_vendor,
      element_reference,
      element_expires_on,
      element_renew_by,
      element_renewal_cost,
      element_currency,
      element_auto_renew,
      element_owner,
      element_notes,
      element_status
    ) VALUES (?, ?, ?, ?, TRY_CAST(? AS DATE), TRY_CAST(? AS DATE), TRY_CAST(? AS DECIMAL(19,5)), ?, ?, ?, ?, ?);
  """
  params = (
    args.get("recid"),
    args["element_name"],
    args["element_category"],
    args.get("element_vendor"),
    args.get("element_reference"),
    args.get("element_expires_on"),
    args.get("element_renew_by"),
    args.get("element_renewal_cost"),
    args.get("element_currency"),
    args.get("element_auto_renew", False),
    args.get("element_owner"),
    args.get("element_notes"),
    args.get("element_status", 1),
    args["element_name"],
    args["element_category"],
    args.get("element_vendor"),
    args.get("element_reference"),
    args.get("element_expires_on"),
    args.get("element_renew_by"),
    args.get("element_renewal_cost"),
    args.get("element_currency"),
    args.get("element_auto_renew", False),
    args.get("element_owner"),
    args.get("element_notes"),
    args.get("element_status", 1),
  )
  return await run_exec(sql, params)


async def delete_renewal_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM system_renewals
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))
