"""MSSQL implementations for rpcdispatch subdomains query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

async def list_subdomains_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_subdomains
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql)

async def get_subdomain_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_subdomains
    WHERE recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))

async def list_by_domain_subdomains_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT *
    FROM reflection_rpc_subdomains
    WHERE domains_recid = ?
    ORDER BY recid
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["domains_recid"],))

async def upsert_subdomain_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (recid bigint);

    MERGE reflection_rpc_subdomains AS target
    USING (SELECT ? AS domains_recid, ? AS element_name, ? AS element_entitlement_mask, ? AS element_status, ? AS element_app_version) AS src
    ON target.recid = TRY_CAST(? AS BIGINT)
    WHEN MATCHED THEN
      UPDATE SET
        target.domains_recid = src.domains_recid,
        target.element_name = src.element_name,
        target.element_entitlement_mask = src.element_entitlement_mask,
        target.element_status = src.element_status,
        target.element_app_version = src.element_app_version,
        target.element_iteration = target.element_iteration + 1,
        target.element_modified_on = SYSUTCDATETIME()
    WHEN NOT MATCHED THEN
      INSERT (domains_recid, element_name, element_entitlement_mask, element_status, element_app_version, element_created_on, element_modified_on)
      VALUES (src.domains_recid, src.element_name, src.element_entitlement_mask, src.element_status, src.element_app_version, SYSUTCDATETIME(), SYSUTCDATETIME())
    OUTPUT inserted.recid INTO @out;

    SELECT t.*
    FROM reflection_rpc_subdomains t
    JOIN @out o ON o.recid = t.recid
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["domains_recid"], args["element_name"], args["element_entitlement_mask"], args["element_status"], args["element_app_version"], args.get("recid")))

async def delete_subdomain_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;
    DECLARE @out TABLE (
      recid bigint,
      element_name nvarchar(64),
      element_status int
    );

    DELETE FROM reflection_rpc_subdomains
    OUTPUT deleted.recid, deleted.element_name, deleted.element_status INTO @out
    WHERE recid = ?;

    SELECT *
    FROM @out
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))
