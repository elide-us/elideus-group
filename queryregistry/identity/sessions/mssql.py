"""MSSQL implementations for identity sessions query registry services."""

from __future__ import annotations

from uuid import UUID

from server.registry.providers.mssql import run_json_many

from queryregistry.models import DBResponse

from .models import SecuritySnapshotRequestPayload

__all__ = [
  "get_security_snapshot_v1",
]


async def get_security_snapshot_v1(params: SecuritySnapshotRequestPayload) -> DBResponse:
  guid = str(UUID(params["guid"]))
  sql = """
    SELECT
      aus.user_guid,
      aus.element_rotkey,
      aus.element_rotkey_iat,
      aus.element_rotkey_exp,
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
