"""MSSQL implementations for finance journals query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

__all__ = ["create_v1", "get_by_posting_key_v1", "get_v1", "list_v1", "update_status_v1"]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("status") is not None:
    where_clauses.append("element_status = ?")
    params.append(args["status"])

  if args.get("periods_guid"):
    where_clauses.append("periods_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)")
    params.append(args["periods_guid"])

  where_sql = ""
  if where_clauses:
    where_sql = "WHERE " + " AND ".join(where_clauses)

  sql = f"""
    SELECT
      recid,
      element_name,
      element_description,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on,
      element_posting_key,
      element_source_type,
      element_source_id,
      periods_guid,
      ledgers_recid,
      element_posted_by,
      element_posted_on,
      element_reversed_by,
      element_reversal_of
    FROM finance_journals
    {where_sql}
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, params)


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on,
      element_posting_key,
      element_source_type,
      element_source_id,
      periods_guid,
      ledgers_recid,
      element_posted_by,
      element_posted_on,
      element_reversed_by,
      element_reversal_of
    FROM finance_journals
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def create_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    INSERT INTO finance_journals (
      element_name,
      element_description,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on,
      element_posting_key,
      element_source_type,
      element_source_id,
      periods_guid,
      ledgers_recid
    )
    OUTPUT
      inserted.recid,
      inserted.element_name,
      inserted.element_description,
      inserted.numbers_recid,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on,
      inserted.element_posting_key,
      inserted.element_source_type,
      inserted.element_source_id,
      inserted.periods_guid,
      inserted.ledgers_recid,
      inserted.element_posted_by,
      inserted.element_posted_on,
      inserted.element_reversed_by,
      inserted.element_reversal_of
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES
    VALUES (?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME(), ?, ?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER), ?);
  """
  params = (
    args["name"],
    args.get("description"),
    args.get("numbers_recid"),
    args["status"],
    args.get("posting_key"),
    args.get("source_type"),
    args.get("source_id"),
    args.get("periods_guid"),
    args.get("ledgers_recid"),
  )
  return await run_json_one(sql, params)


async def update_status_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    UPDATE finance_journals
    SET
      element_status = ?,
      element_posted_by = TRY_CAST(? AS UNIQUEIDENTIFIER),
      element_posted_on = TRY_CAST(? AS DATETIMEOFFSET(7)),
      element_reversed_by = ?,
      element_reversal_of = ?,
      element_modified_on = SYSUTCDATETIME()
    OUTPUT
      inserted.recid,
      inserted.element_name,
      inserted.element_description,
      inserted.numbers_recid,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on,
      inserted.element_posting_key,
      inserted.element_source_type,
      inserted.element_source_id,
      inserted.periods_guid,
      inserted.ledgers_recid,
      inserted.element_posted_by,
      inserted.element_posted_on,
      inserted.element_reversed_by,
      inserted.element_reversal_of
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES
    WHERE recid = ?;
  """
  params = (
    args["status"],
    args.get("posted_by"),
    args.get("posted_on"),
    args.get("reversed_by"),
    args.get("reversal_of"),
    args["recid"],
  )
  return await run_json_one(sql, params)


async def get_by_posting_key_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_name,
      element_description,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on,
      element_posting_key,
      element_source_type,
      element_source_id,
      periods_guid,
      ledgers_recid,
      element_posted_by,
      element_posted_on,
      element_reversed_by,
      element_reversal_of
    FROM finance_journals
    WHERE element_posting_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["posting_key"],))
