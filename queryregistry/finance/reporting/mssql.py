"""MSSQL implementations for finance reporting query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many

__all__ = [
  "credit_lot_summary_v1",
  "journal_summary_v1",
  "period_status_v1",
  "trial_balance_v1",
]


async def trial_balance_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("fiscal_year") is not None:
    where_clauses.append("fiscal_year = ?")
    params.append(args["fiscal_year"])

  if args.get("period_guid"):
    where_clauses.append("period_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)")
    params.append(args["period_guid"])

  where_sql = ""
  if where_clauses:
    where_sql = "WHERE " + " AND ".join(where_clauses)

  sql = f"""
    SELECT *
    FROM vw_finance_trial_balance
    {where_sql}
    ORDER BY account_number
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, params)


async def journal_summary_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("journal_status") is not None:
    where_clauses.append("journal_status = ?")
    params.append(args["journal_status"])

  if args.get("fiscal_year") is not None:
    where_clauses.append("fiscal_year = ?")
    params.append(args["fiscal_year"])

  if args.get("periods_guid"):
    where_clauses.append("periods_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)")
    params.append(args["periods_guid"])

  where_sql = ""
  if where_clauses:
    where_sql = "WHERE " + " AND ".join(where_clauses)

  sql = f"""
    SELECT *
    FROM vw_finance_journal_summary
    {where_sql}
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, params)


async def period_status_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("fiscal_year") is not None:
    where_clauses.append("fiscal_year = ?")
    params.append(args["fiscal_year"])

  where_sql = ""
  if where_clauses:
    where_sql = "WHERE " + " AND ".join(where_clauses)

  sql = f"""
    SELECT *
    FROM vw_finance_period_status
    {where_sql}
    ORDER BY fiscal_year DESC, period_number DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, params)


async def credit_lot_summary_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("users_guid"):
    where_clauses.append("users_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)")
    params.append(args["users_guid"])

  where_sql = ""
  if where_clauses:
    where_sql = "WHERE " + " AND ".join(where_clauses)

  sql = f"""
    SELECT *
    FROM vw_finance_credit_lot_summary
    {where_sql}
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, params)
