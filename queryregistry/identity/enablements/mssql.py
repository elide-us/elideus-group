"""MSSQL implementations for identity enablements query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_one

__all__ = ["get_v1", "upsert_v1"]


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT TOP 1
      users_guid,
      element_enablements,
      element_created_on,
      element_modified_on
    FROM users_enablements
    WHERE users_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["users_guid"],))


async def upsert_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @result TABLE (
      users_guid UNIQUEIDENTIFIER,
      element_enablements NVARCHAR(64),
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    MERGE users_enablements AS target
    USING (
      SELECT
        TRY_CAST(? AS UNIQUEIDENTIFIER) AS users_guid,
        ? AS element_enablements
    ) AS source
    ON target.users_guid = source.users_guid
    WHEN MATCHED THEN
      UPDATE SET
        target.element_enablements = source.element_enablements,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (users_guid, element_enablements, element_created_on, element_modified_on)
      VALUES (source.users_guid, source.element_enablements, SYSUTCDATETIME(), SYSUTCDATETIME())
    OUTPUT
      inserted.users_guid,
      inserted.element_enablements,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result;

    SELECT * FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["users_guid"], args["element_enablements"]))
