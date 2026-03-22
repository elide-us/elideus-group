"""MSSQL implementations for finance products query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = ["delete_v1", "get_v1", "list_v1", "upsert_v1"]

_PRODUCT_SELECT = """
    SELECT
      recid,
      element_sku,
      element_name,
      element_description,
      element_category,
      element_price,
      element_currency,
      element_credits,
      element_enablement_key,
      element_is_recurring,
      element_sort_order,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_products
"""


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = f"""
{_PRODUCT_SELECT}
    WHERE (? IS NULL OR element_category = ?)
      AND (? IS NULL OR element_status = ?)
    ORDER BY element_sort_order ASC, element_name ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  category = args.get("category")
  status = args.get("status")
  return await run_json_many(sql, (category, category, status, status))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  if args.get("recid") is not None:
    sql = f"""
{_PRODUCT_SELECT}
    WHERE recid = TRY_CAST(? AS BIGINT)
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
    """
    return await run_json_one(sql, (args["recid"],))

  sql = f"""
{_PRODUCT_SELECT}
    WHERE element_sku = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["sku"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @result TABLE (
      recid BIGINT,
      element_sku NVARCHAR(32),
      element_name NVARCHAR(200),
      element_description NVARCHAR(512),
      element_category NVARCHAR(64),
      element_price DECIMAL(19,5),
      element_currency NVARCHAR(3),
      element_credits INT,
      element_enablement_key NVARCHAR(64),
      element_is_recurring BIT,
      element_sort_order INT,
      element_status TINYINT,
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    MERGE finance_products AS target
    USING (
      SELECT
        TRY_CAST(? AS BIGINT) AS recid,
        ? AS element_sku,
        ? AS element_name,
        ? AS element_description,
        ? AS element_category,
        TRY_CAST(? AS DECIMAL(19,5)) AS element_price,
        ? AS element_currency,
        ? AS element_credits,
        ? AS element_enablement_key,
        ? AS element_is_recurring,
        ? AS element_sort_order,
        ? AS element_status
    ) AS source
    ON (source.recid IS NOT NULL AND target.recid = source.recid)
      OR (source.recid IS NULL AND target.element_sku = source.element_sku)
    WHEN MATCHED THEN
      UPDATE SET
        target.element_sku = source.element_sku,
        target.element_name = source.element_name,
        target.element_description = source.element_description,
        target.element_category = source.element_category,
        target.element_price = source.element_price,
        target.element_currency = source.element_currency,
        target.element_credits = source.element_credits,
        target.element_enablement_key = source.element_enablement_key,
        target.element_is_recurring = source.element_is_recurring,
        target.element_sort_order = source.element_sort_order,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_sku,
        element_name,
        element_description,
        element_category,
        element_price,
        element_currency,
        element_credits,
        element_enablement_key,
        element_is_recurring,
        element_sort_order,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_sku,
        source.element_name,
        source.element_description,
        source.element_category,
        source.element_price,
        source.element_currency,
        source.element_credits,
        source.element_enablement_key,
        source.element_is_recurring,
        source.element_sort_order,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.element_sku,
      inserted.element_name,
      inserted.element_description,
      inserted.element_category,
      inserted.element_price,
      inserted.element_currency,
      inserted.element_credits,
      inserted.element_enablement_key,
      inserted.element_is_recurring,
      inserted.element_sort_order,
      inserted.element_status,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result;

    SELECT *
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args.get("recid"),
    args["sku"],
    args["name"],
    args.get("description"),
    args["category"],
    args["price"],
    args["currency"],
    args["credits"],
    args.get("enablement_key"),
    args["is_recurring"],
    args["sort_order"],
    args["status"],
  )
  return await run_json_one(sql, params)


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_products
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))
