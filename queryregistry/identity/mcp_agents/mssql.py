"""MSSQL implementations for identity MCP agents query registry services."""

from __future__ import annotations

from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from .models import (
  AgentRecidParams,
  ClientIdParams,
  CreateAgentTokenParams,
  CreateAuthCodeParams,
  ConsumeAuthCodeParams,
  LinkAgentUserParams,
  RefreshTokenParams,
  RegisterAgentParams,
  RevokeTokenParams,
  UserGuidParams,
)

__all__ = [
  "consume_auth_code_v1",
  "create_auth_code_v1",
  "create_token_v1",
  "get_by_client_id_v1",
  "get_by_recid_v1",
  "get_token_v1",
  "link_user_v1",
  "list_by_user_v1",
  "register_v1",
  "revoke_token_v1",
  "revoke_v1",
]


async def register_v1(args: dict[str, Any]) -> DBResponse:
  params = RegisterAgentParams.model_validate(args)
  sql = """
    SET NOCOUNT ON;
    DECLARE @inserted TABLE (
      recid bigint,
      element_client_id uniqueidentifier,
      element_client_name nvarchar(256),
      element_scopes nvarchar(1024),
      element_created_on datetimeoffset(7)
    );

    INSERT INTO account_mcp_agents (
      element_client_name,
      element_redirect_uris,
      element_grant_types,
      element_response_types,
      element_scopes,
      element_ip_address,
      element_user_agent
    )
    OUTPUT
      inserted.recid,
      inserted.element_client_id,
      inserted.element_client_name,
      inserted.element_scopes,
      inserted.element_created_on
    INTO @inserted
    VALUES (?, ?, ?, ?, ?, ?, ?);

    SELECT *
    FROM @inserted
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(
    sql,
    (
      params.client_name,
      params.redirect_uris,
      params.grant_types,
      params.response_types,
      params.scopes,
      params.ip_address,
      params.user_agent,
    ),
  )


async def get_by_client_id_v1(args: dict[str, Any]) -> DBResponse:
  params = ClientIdParams.model_validate(args)
  sql = """
    SELECT
      a.recid,
      a.element_client_id,
      a.element_client_name,
      a.element_scopes,
      a.element_roles,
      a.users_guid,
      a.element_is_active,
      a.element_revoked_at,
      a.element_redirect_uris,
      a.users_guid AS user_guid
    FROM account_mcp_agents a
    LEFT JOIN account_users au ON au.element_guid = a.users_guid
    WHERE a.element_client_id = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (params.client_id,))


async def get_by_recid_v1(args: dict[str, Any]) -> DBResponse:
  params = AgentRecidParams.model_validate(args)
  sql = """
    SELECT
      a.recid,
      a.element_client_id,
      a.element_client_name,
      a.element_scopes,
      a.element_roles,
      a.users_guid,
      a.element_is_active,
      a.element_revoked_at,
      a.element_redirect_uris,
      a.users_guid AS user_guid
    FROM account_mcp_agents a
    LEFT JOIN account_users au ON au.element_guid = a.users_guid
    WHERE a.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (params.agents_recid,))


async def link_user_v1(args: dict[str, Any]) -> DBResponse:
  params = LinkAgentUserParams.model_validate(args)
  sql = """
    UPDATE account_mcp_agents
    SET users_guid = ?, element_modified_on = SYSUTCDATETIME()
    WHERE element_client_id = ?;
  """
  return await run_exec(sql, (params.users_guid, params.client_id))


async def revoke_v1(args: dict[str, Any]) -> DBResponse:
  params = ClientIdParams.model_validate(args)
  sql = """
    UPDATE account_mcp_agents
    SET element_is_active = 0,
        element_revoked_at = SYSUTCDATETIME(),
        element_modified_on = SYSUTCDATETIME()
    WHERE element_client_id = ?;
  """
  return await run_exec(sql, (params.client_id,))


async def list_by_user_v1(args: dict[str, Any]) -> DBResponse:
  params = UserGuidParams.model_validate(args)
  sql = """
    SELECT
      recid,
      element_client_id,
      element_client_name,
      element_redirect_uris,
      element_grant_types,
      element_response_types,
      element_scopes,
      element_roles,
      users_guid,
      element_is_active,
      element_revoked_at,
      element_created_on,
      element_modified_on
    FROM account_mcp_agents
    WHERE users_guid = ?
    ORDER BY recid DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (params.users_guid,))


async def create_auth_code_v1(args: dict[str, Any]) -> DBResponse:
  params = CreateAuthCodeParams.model_validate(args)
  sql = """
    SET NOCOUNT ON;
    DECLARE @inserted TABLE (
      recid bigint,
      agents_recid bigint,
      users_guid uniqueidentifier,
      element_code nvarchar(256),
      element_expires_on datetimeoffset(7)
    );

    INSERT INTO account_mcp_auth_codes (
      agents_recid,
      users_guid,
      element_code,
      element_code_challenge,
      element_code_method,
      element_redirect_uri,
      element_scopes,
      element_expires_on
    )
    OUTPUT
      inserted.recid,
      inserted.agents_recid,
      inserted.users_guid,
      inserted.element_code,
      inserted.element_expires_on
    INTO @inserted
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);

    SELECT *
    FROM @inserted
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(
    sql,
    (
      params.agents_recid,
      params.users_guid,
      params.code,
      params.code_challenge,
      params.code_method,
      params.redirect_uri,
      params.scopes,
      params.expires_on,
    ),
  )


async def consume_auth_code_v1(args: dict[str, Any]) -> DBResponse:
  params = ConsumeAuthCodeParams.model_validate(args)
  sql = """
    SET NOCOUNT ON;
    DECLARE @consumed TABLE (
      recid bigint,
      agents_recid bigint,
      users_guid uniqueidentifier,
      element_code_challenge nvarchar(256),
      element_code_method nvarchar(16),
      element_redirect_uri nvarchar(2048),
      element_scopes nvarchar(1024),
      element_expires_on datetimeoffset(7)
    );

    UPDATE account_mcp_auth_codes
    SET element_consumed = 1
    OUTPUT
      inserted.recid,
      inserted.agents_recid,
      inserted.users_guid,
      inserted.element_code_challenge,
      inserted.element_code_method,
      inserted.element_redirect_uri,
      inserted.element_scopes,
      inserted.element_expires_on
    INTO @consumed
    WHERE element_code = ?
      AND element_consumed = 0
      AND element_expires_on > SYSUTCDATETIME();

    SELECT TOP 1 *
    FROM @consumed
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (params.code,))


async def create_token_v1(args: dict[str, Any]) -> DBResponse:
  params = CreateAgentTokenParams.model_validate(args)
  sql = """
    SET NOCOUNT ON;
    DECLARE @inserted TABLE (
      recid bigint,
      agents_recid bigint,
      element_access_exp datetimeoffset(7),
      element_refresh_exp datetimeoffset(7),
      element_scopes nvarchar(1024),
      element_created_on datetimeoffset(7)
    );

    INSERT INTO account_mcp_agent_tokens (
      agents_recid,
      element_access_token,
      element_refresh_token,
      element_access_exp,
      element_refresh_exp,
      element_scopes
    )
    OUTPUT
      inserted.recid,
      inserted.agents_recid,
      inserted.element_access_exp,
      inserted.element_refresh_exp,
      inserted.element_scopes,
      inserted.element_created_on
    INTO @inserted
    VALUES (?, ?, ?, ?, ?, ?);

    SELECT TOP 1 *
    FROM @inserted
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(
    sql,
    (
      params.agents_recid,
      params.access_token,
      params.refresh_token,
      params.access_exp,
      params.refresh_exp,
      params.scopes,
    ),
  )


async def get_token_v1(args: dict[str, Any]) -> DBResponse:
  params = RefreshTokenParams.model_validate(args)
  sql = """
    SELECT TOP 1
      t.recid,
      t.agents_recid,
      t.element_refresh_token,
      t.element_refresh_exp,
      t.element_scopes,
      t.element_revoked_at,
      a.element_client_id,
      a.users_guid,
      a.element_is_active,
      a.users_guid AS user_guid
    FROM account_mcp_agent_tokens t
    JOIN account_mcp_agents a ON a.recid = t.agents_recid
    WHERE t.element_refresh_token = ?
      AND t.element_revoked_at IS NULL
    ORDER BY t.recid DESC
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (params.refresh_token,))


async def revoke_token_v1(args: dict[str, Any]) -> DBResponse:
  params = RevokeTokenParams.model_validate(args)
  sql = """
    UPDATE account_mcp_agent_tokens
    SET element_revoked_at = SYSUTCDATETIME()
    WHERE agents_recid = ? AND element_revoked_at IS NULL;
  """
  return await run_exec(sql, (params.agents_recid,))
