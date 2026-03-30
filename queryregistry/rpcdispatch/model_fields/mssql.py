"""MSSQL implementations for rpcdispatch model_fields query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

async def list_model_fields_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_model_fields
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)

async def get_model_field_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_model_fields
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))

async def list_by_model_model_fields_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_model_fields
    WHERE models_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["models_guid"],))

async def upsert_model_field_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (recid bigint);

    MERGE reflection_rpc_model_fields AS target
    USING (SELECT TRY_CAST(? AS UNIQUEIDENTIFIER) AS models_guid, ? AS element_name, ? AS element_edt_recid, ? AS element_is_nullable, ? AS element_is_list, ? AS element_is_dict, TRY_CAST(? AS UNIQUEIDENTIFIER) AS element_ref_model_guid, ? AS element_default_value, ? AS element_max_length, ? AS element_sort_order, ? AS element_status) AS src
    ON target.recid = TRY_CAST(? AS BIGINT)
    WHEN MATCHED THEN
      UPDATE SET
        target.models_guid = src.models_guid,
        target.element_name = src.element_name,
        target.element_edt_recid = src.element_edt_recid,
        target.element_is_nullable = src.element_is_nullable,
        target.element_is_list = src.element_is_list,
        target.element_is_dict = src.element_is_dict,
        target.element_ref_model_guid = src.element_ref_model_guid,
        target.element_default_value = src.element_default_value,
        target.element_max_length = src.element_max_length,
        target.element_sort_order = src.element_sort_order,
        target.element_status = src.element_status,
        target.element_iteration = target.element_iteration + 1,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (models_guid, element_name, element_edt_recid, element_is_nullable, element_is_list, element_is_dict, element_ref_model_guid, element_default_value, element_max_length, element_sort_order, element_status, element_created_on, element_modified_on)
      VALUES (src.models_guid, src.element_name, src.element_edt_recid, src.element_is_nullable, src.element_is_list, src.element_is_dict, src.element_ref_model_guid, src.element_default_value, src.element_max_length, src.element_sort_order, src.element_status, SYSUTCDATETIME(), SYSUTCDATETIME())
    OUTPUT inserted.recid INTO @out;

    SELECT t.*
    FROM reflection_rpc_model_fields t
    JOIN @out o ON o.recid = t.recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["models_guid"], args["element_name"], args["element_edt_recid"], args["element_is_nullable"], args["element_is_list"], args["element_is_dict"], args["element_ref_model_guid"], args["element_default_value"], args["element_max_length"], args["element_sort_order"], args["element_status"], args.get("recid")))

async def delete_model_field_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (
      recid bigint,
      element_name nvarchar(128),
      element_status int
    );

    DELETE FROM reflection_rpc_model_fields
    OUTPUT deleted.recid, deleted.element_name, deleted.element_status INTO @out
    WHERE recid = ?;

    SELECT *
    FROM @out
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))
