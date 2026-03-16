"""MSSQL implementations for finance credit lots query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "consume_credits_v1",
  "create_event_v1",
  "create_lot_v1",
  "expire_lot_v1",
  "get_lot_v1",
  "list_events_by_lot_v1",
  "list_lots_by_user_v1",
  "sum_remaining_by_user_v1",
]


async def list_lots_by_user_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      users_guid,
      element_lot_number,
      element_source_type,
      element_credits_original,
      element_credits_remaining,
      element_unit_price,
      element_total_paid,
      element_currency,
      element_expires_at,
      element_expired,
      element_source_id,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_credit_lots
    WHERE users_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_expired = 0
      AND element_credits_remaining > 0
      AND element_status = 1
    ORDER BY recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["users_guid"],))


async def get_lot_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      users_guid,
      element_lot_number,
      element_source_type,
      element_credits_original,
      element_credits_remaining,
      element_unit_price,
      element_total_paid,
      element_currency,
      element_expires_at,
      element_expired,
      element_source_id,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_credit_lots
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def create_lot_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid bigint,
      users_guid uniqueidentifier,
      element_lot_number nvarchar(64),
      element_source_type nvarchar(64),
      element_credits_original int,
      element_credits_remaining int,
      element_unit_price decimal(19,5),
      element_total_paid decimal(19,5),
      element_currency nvarchar(3),
      element_expires_at datetimeoffset,
      element_expired bit,
      element_source_id nvarchar(256),
      numbers_recid bigint,
      element_status tinyint,
      element_created_on datetimeoffset,
      element_modified_on datetimeoffset
    );

    INSERT INTO finance_credit_lots (
      users_guid,
      element_lot_number,
      element_source_type,
      element_credits_original,
      element_credits_remaining,
      element_unit_price,
      element_total_paid,
      element_currency,
      element_expires_at,
      element_expired,
      element_source_id,
      numbers_recid,
      element_status,
      element_created_on,
      element_modified_on
    )
    OUTPUT
      inserted.recid,
      inserted.users_guid,
      inserted.element_lot_number,
      inserted.element_source_type,
      inserted.element_credits_original,
      inserted.element_credits_remaining,
      inserted.element_unit_price,
      inserted.element_total_paid,
      inserted.element_currency,
      inserted.element_expires_at,
      inserted.element_expired,
      inserted.element_source_id,
      inserted.numbers_recid,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result
    VALUES (
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      ?,
      ?,
      ?,
      ?,
      CAST(? AS DECIMAL(19,5)),
      CAST(? AS DECIMAL(19,5)),
      ?,
      TRY_CAST(? AS DATETIMEOFFSET(7)),
      0,
      ?,
      ?,
      ?,
      SYSUTCDATETIME(),
      SYSUTCDATETIME()
    );

    SELECT * FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["users_guid"],
    args["lot_number"],
    args["source_type"],
    args["credits_original"],
    args["credits_remaining"],
    args["unit_price"],
    args["total_paid"],
    args["currency"],
    args.get("expires_at"),
    args.get("source_id"),
    args.get("numbers_recid"),
    args["status"],
  )
  return await run_json_one(sql, params)


async def consume_credits_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    UPDATE finance_credit_lots
    SET
      element_credits_remaining = element_credits_remaining - ?,
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?
      AND element_credits_remaining >= ?;
  """
  return await run_exec(
    sql,
    (args["credits_to_consume"], args["recid"], args["credits_to_consume"]),
  )


async def expire_lot_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    UPDATE finance_credit_lots
    SET
      element_expired = 1,
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))


async def list_events_by_lot_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      lots_recid,
      element_event_type,
      element_credits,
      element_unit_price,
      element_description,
      element_actor_guid,
      journals_recid,
      element_created_on
    FROM finance_credit_lot_events
    WHERE lots_recid = ?
    ORDER BY recid ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["lots_recid"],))


async def create_event_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid bigint,
      lots_recid bigint,
      element_event_type nvarchar(32),
      element_credits int,
      element_unit_price decimal(19,5),
      element_description nvarchar(512),
      element_actor_guid uniqueidentifier,
      journals_recid bigint,
      element_created_on datetimeoffset
    );

    INSERT INTO finance_credit_lot_events (
      lots_recid,
      element_event_type,
      element_credits,
      element_unit_price,
      element_description,
      element_actor_guid,
      journals_recid,
      element_created_on
    )
    OUTPUT
      inserted.recid,
      inserted.lots_recid,
      inserted.element_event_type,
      inserted.element_credits,
      inserted.element_unit_price,
      inserted.element_description,
      inserted.element_actor_guid,
      inserted.journals_recid,
      inserted.element_created_on
    INTO @result
    VALUES (
      ?,
      ?,
      ?,
      CAST(? AS DECIMAL(19,5)),
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      ?,
      SYSUTCDATETIME()
    );

    SELECT * FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["lots_recid"],
    args["event_type"],
    args["credits"],
    args["unit_price"],
    args.get("description"),
    args.get("actor_guid"),
    args.get("journals_recid"),
  )
  return await run_json_one(sql, params)


async def sum_remaining_by_user_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT ISNULL(SUM(element_credits_remaining), 0) AS total_remaining
    FROM finance_credit_lots
    WHERE users_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      AND element_expired = 0
      AND element_status = 1
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["users_guid"],))
