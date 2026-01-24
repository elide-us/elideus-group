"""MSSQL implementations for identity sessions query registry services."""

from __future__ import annotations

from uuid import UUID

from queryregistry.providers.mssql import run_json_many, run_json_one

from queryregistry.models import DBResponse

from .models import RotkeyRequestPayload, SecuritySnapshotRequestPayload

__all__ = [
  "get_rotkey_v1",
  "get_security_snapshot_v1",
]


async def get_rotkey_v1(params: RotkeyRequestPayload) -> DBResponse:
  guid = str(UUID(params["guid"]))
  device_guid = params.get("device_guid")
  fingerprint = params.get("fingerprint")
  sql = """
    SELECT TOP 1
      au.element_guid AS user_guid,
      au.element_rotkey AS user_rotkey,
      au.element_rotkey_iat AS user_rotkey_iat,
      au.element_rotkey_exp AS user_rotkey_exp,
      ap.element_name AS provider_name,
      ap.element_display AS provider_display,
      latest.session_guid,
      latest.session_created_on,
      latest.session_modified_on,
      latest.device_guid,
      latest.device_token,
      latest.device_token_iat,
      latest.device_token_exp,
      latest.revoked_at,
      latest.device_fingerprint,
      latest.user_agent,
      latest.ip_last_seen,
      latest.device_rotkey,
      latest.device_rotkey_iat,
      latest.device_rotkey_exp
    FROM account_users au
    LEFT JOIN auth_providers ap ON ap.recid = au.providers_recid
    OUTER APPLY (
      SELECT TOP 1
        us.element_guid AS session_guid,
        us.element_created_on AS session_created_on,
        us.element_modified_on AS session_modified_on,
        sd.element_guid AS device_guid,
        sd.element_token AS device_token,
        sd.element_token_iat AS device_token_iat,
        sd.element_token_exp AS device_token_exp,
        sd.element_revoked_at AS revoked_at,
        sd.element_device_fingerprint AS device_fingerprint,
        sd.element_user_agent AS user_agent,
        sd.element_ip_last_seen AS ip_last_seen,
        sd.element_rotkey AS device_rotkey,
        sd.element_rotkey_iat AS device_rotkey_iat,
        sd.element_rotkey_exp AS device_rotkey_exp
      FROM users_sessions us
      JOIN sessions_devices sd ON sd.sessions_guid = us.element_guid
      WHERE us.users_guid = au.element_guid
        AND (? IS NULL OR sd.element_guid = ?)
        AND (? IS NULL OR sd.element_device_fingerprint = ?)
      ORDER BY sd.element_token_iat DESC
    ) latest
    WHERE au.element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (device_guid, device_guid, fingerprint, fingerprint, guid))
  return DBResponse(payload=response.payload)


async def get_security_snapshot_v1(params: SecuritySnapshotRequestPayload) -> DBResponse:
  guid = str(UUID(params["guid"]))
  sql = """
    SELECT
      aus.user_guid,
      aus.element_rotkey,
      aus.element_rotkey_iat,
      aus.element_rotkey_exp,
      aus.element_device_rotkey,
      aus.element_device_rotkey_iat,
      aus.element_device_rotkey_exp,
      aus.session_guid,
      aus.device_guid,
      aus.element_token,
      aus.element_token_iat,
      aus.element_token_exp,
      aus.element_revoked_at,
      aus.element_device_fingerprint,
      aus.element_user_agent,
      aus.element_ip_last_seen
    FROM vw_user_session_security aus
    WHERE aus.user_guid = ?
    ORDER BY aus.element_token_iat DESC
    FOR JSON PATH;
  """
  response = await run_json_many(sql, (guid,))
  return DBResponse(payload=response.payload)
