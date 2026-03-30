"""MSSQL implementations for rpcdispatch functions query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

async def list_functions_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_functions
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)

async def get_function_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_functions
    WHERE (TRY_CAST(? AS BIGINT) IS NOT NULL AND recid = TRY_CAST(? AS BIGINT))
       OR element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args.get("recid"), args.get("recid"), args.get("guid")))

async def list_by_subdomain_functions_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_functions
    WHERE subdomains_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["subdomains_guid"],))

async def upsert_function_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (recid bigint);

    MERGE reflection_rpc_functions AS target
    USING (SELECT TRY_CAST(? AS UNIQUEIDENTIFIER) AS subdomains_guid, ? AS element_name, ? AS element_version, ? AS element_module_attr, ? AS element_method_name, TRY_CAST(? AS UNIQUEIDENTIFIER) AS element_request_model_guid, TRY_CAST(? AS UNIQUEIDENTIFIER) AS element_response_model_guid, ? AS element_status, ? AS element_app_version) AS src
    ON target.recid = TRY_CAST(? AS BIGINT)
    WHEN MATCHED THEN
      UPDATE SET
        target.subdomains_guid = src.subdomains_guid,
        target.element_name = src.element_name,
        target.element_version = src.element_version,
        target.element_module_attr = src.element_module_attr,
        target.element_method_name = src.element_method_name,
        target.element_request_model_guid = src.element_request_model_guid,
        target.element_response_model_guid = src.element_response_model_guid,
        target.element_status = src.element_status,
        target.element_app_version = src.element_app_version,
        target.element_iteration = target.element_iteration + 1,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (subdomains_guid, element_name, element_version, element_module_attr, element_method_name, element_request_model_guid, element_response_model_guid, element_status, element_app_version, element_created_on, element_modified_on)
      VALUES (src.subdomains_guid, src.element_name, src.element_version, src.element_module_attr, src.element_method_name, src.element_request_model_guid, src.element_response_model_guid, src.element_status, src.element_app_version, SYSUTCDATETIME(), SYSUTCDATETIME())
    OUTPUT inserted.recid INTO @out;

    SELECT t.*
    FROM reflection_rpc_functions t
    JOIN @out o ON o.recid = t.recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["subdomains_guid"], args["element_name"], args["element_version"], args["element_module_attr"], args["element_method_name"], args["element_request_model_guid"], args["element_response_model_guid"], args["element_status"], args["element_app_version"], args.get("recid")))

async def delete_function_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (
      recid bigint,
      element_name nvarchar(128),
      element_status int
    );

    DELETE FROM reflection_rpc_functions
    OUTPUT deleted.recid, deleted.element_name, deleted.element_status INTO @out
    WHERE recid = ?;

    SELECT *
    FROM @out
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))
