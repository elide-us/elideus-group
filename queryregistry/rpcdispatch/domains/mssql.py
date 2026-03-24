"""MSSQL implementations for rpcdispatch domains query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

async def list_domains_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_domains
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)

async def get_domain_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_domains
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))

async def get_by_name_domains_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_domains
    WHERE element_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_name"],))

async def upsert_domain_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (recid bigint);

    MERGE reflection_rpc_domains AS target
    USING (SELECT ? AS element_name, ? AS element_required_role, ? AS element_is_auth_exempt, ? AS element_is_public, ? AS element_is_discord, ? AS element_status, ? AS element_app_version) AS src
    ON target.recid = TRY_CAST(? AS BIGINT)
    WHEN MATCHED THEN
      UPDATE SET
        target.element_name = src.element_name,
        target.element_required_role = src.element_required_role,
        target.element_is_auth_exempt = src.element_is_auth_exempt,
        target.element_is_public = src.element_is_public,
        target.element_is_discord = src.element_is_discord,
        target.element_status = src.element_status,
        target.element_app_version = src.element_app_version,
        target.element_iteration = target.element_iteration + 1,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (element_name, element_required_role, element_is_auth_exempt, element_is_public, element_is_discord, element_status, element_app_version, element_created_on, element_modified_on)
      VALUES (src.element_name, src.element_required_role, src.element_is_auth_exempt, src.element_is_public, src.element_is_discord, src.element_status, src.element_app_version, SYSUTCDATETIME(), SYSUTCDATETIME())
    OUTPUT inserted.recid INTO @out;

    SELECT t.*
    FROM reflection_rpc_domains t
    JOIN @out o ON o.recid = t.recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_name"], args["element_required_role"], args["element_is_auth_exempt"], args["element_is_public"], args["element_is_discord"], args["element_status"], args["element_app_version"], args.get("recid")))

async def delete_domain_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @deleted TABLE (recid bigint);

    DELETE FROM reflection_rpc_domains
    OUTPUT deleted.recid INTO @deleted
    WHERE recid = ?;

    SELECT t.*
    FROM reflection_rpc_domains t
    JOIN @deleted d ON d.recid = t.recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))
