"""MSSQL implementations for finance pipeline config query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "delete_pipeline_config_v1",
  "get_pipeline_config_v1",
  "list_pipeline_configs_v1",
  "upsert_pipeline_config_v1",
]


async def list_pipeline_configs_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_pipeline,
      element_key,
      element_value,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_pipeline_config
    WHERE (? IS NULL OR element_pipeline = ?)
    ORDER BY element_pipeline, element_key
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  element_pipeline = args.get("element_pipeline")
  return await run_json_many(sql, (element_pipeline, element_pipeline))


async def get_pipeline_config_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_pipeline,
      element_key,
      element_value,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_pipeline_config
    WHERE element_pipeline = ?
      AND element_key = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_pipeline"], args["element_key"]))


async def upsert_pipeline_config_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @result TABLE (
      recid BIGINT,
      element_pipeline NVARCHAR(64),
      element_key NVARCHAR(128),
      element_value NVARCHAR(512),
      element_description NVARCHAR(512),
      element_status TINYINT,
      element_created_on DATETIMEOFFSET(7),
      element_modified_on DATETIMEOFFSET(7)
    );

    MERGE finance_pipeline_config AS target
    USING (
      SELECT
        TRY_CAST(? AS BIGINT) AS recid,
        ? AS element_pipeline,
        ? AS element_key,
        ? AS element_value,
        ? AS element_description,
        ? AS element_status
    ) AS source
    ON (source.recid IS NOT NULL AND target.recid = source.recid)
      OR (
        source.recid IS NULL
        AND target.element_pipeline = source.element_pipeline
        AND target.element_key = source.element_key
      )
    WHEN MATCHED THEN
      UPDATE SET
        target.element_pipeline = source.element_pipeline,
        target.element_key = source.element_key,
        target.element_value = source.element_value,
        target.element_description = source.element_description,
        target.element_status = source.element_status,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (
        element_pipeline,
        element_key,
        element_value,
        element_description,
        element_status,
        element_created_on,
        element_modified_on
      )
      VALUES (
        source.element_pipeline,
        source.element_key,
        source.element_value,
        source.element_description,
        source.element_status,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      )
    OUTPUT
      inserted.recid,
      inserted.element_pipeline,
      inserted.element_key,
      inserted.element_value,
      inserted.element_description,
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
    args["element_pipeline"],
    args["element_key"],
    args["element_value"],
    args.get("element_description"),
    args["element_status"],
  )
  return await run_json_one(sql, params)


async def delete_pipeline_config_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DELETE FROM finance_pipeline_config
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["recid"],))
