"""MSSQL implementations for system public_vars query registry services."""

from __future__ import annotations

from server.registry.providers.mssql import run_json_one

from queryregistry.models import DBResponse

__all__ = [
  "get_hostname",
  "get_repo",
  "get_version",
]


def _normalize_payload(rows: list[object]) -> dict:
  if not rows:
    return {}
  return dict(rows[0])


async def get_hostname() -> DBResponse:
  sql = """
    SELECT element_value AS hostname
    FROM system_config
    WHERE element_key = 'hostname'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql)
  return DBResponse(payload=_normalize_payload(response.rows))


async def get_version() -> DBResponse:
  sql = """
    SELECT element_value AS version
    FROM system_config
    WHERE element_key = 'version'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql)
  return DBResponse(payload=_normalize_payload(response.rows))


async def get_repo() -> DBResponse:
  sql = """
    SELECT element_value AS repo
    FROM system_config
    WHERE element_key = 'repo'
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql)
  return DBResponse(payload=_normalize_payload(response.rows))
