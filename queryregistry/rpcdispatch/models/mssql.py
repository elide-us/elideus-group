"""MSSQL implementations for rpcdispatch models query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

async def list_models_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_models
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)

async def get_model_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_models
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))

async def get_by_name_models_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_models
    WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_name"],))

async def upsert_model_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (recid bigint);

    MERGE reflection_rpc_models AS target
    USING (SELECT ? AS element_name, ? AS element_domain, ? AS element_subdomain, ? AS element_version, ? AS element_parent_recid, ? AS element_status, ? AS element_app_version) AS src
    ON target.recid = TRY_CAST(? AS BIGINT)
    WHEN MATCHED THEN
      UPDATE SET
        target.element_name = src.element_name,
        target.element_domain = src.element_domain,
        target.element_subdomain = src.element_subdomain,
        target.element_version = src.element_version,
        target.element_parent_recid = src.element_parent_recid,
        target.element_status = src.element_status,
        target.element_app_version = src.element_app_version,
        target.element_iteration = target.element_iteration + 1,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (element_name, element_domain, element_subdomain, element_version, element_parent_recid, element_status, element_app_version, element_created_on, element_modified_on)
      VALUES (src.element_name, src.element_domain, src.element_subdomain, src.element_version, src.element_parent_recid, src.element_status, src.element_app_version, SYSUTCDATETIME(), SYSUTCDATETIME())
    OUTPUT inserted.recid INTO @out;

    SELECT t.*
    FROM reflection_rpc_models t
    JOIN @out o ON o.recid = t.recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_name"], args["element_domain"], args["element_subdomain"], args["element_version"], args["element_parent_recid"], args["element_status"], args["element_app_version"], args.get("recid")))

async def delete_model_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (
      recid bigint,
      element_name nvarchar(128),
      element_status int
    );

    DELETE FROM reflection_rpc_models
    OUTPUT deleted.recid, deleted.element_name, deleted.element_status INTO @out
    WHERE recid = ?;

    SELECT *
    FROM @out
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))
