"""MSSQL helpers for auth provider metadata."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "get_auth_provider_recid",
  "unlink_last_provider_v1",
]


async def get_auth_provider_recid(provider: str, *, cursor=None) -> int:
  """Return the auth provider recid for ``provider`` or raise a uniform error."""
  if cursor is not None:
    await cursor.execute(
      "SELECT recid FROM auth_providers WHERE element_name = ?;",
      (provider,),
    )
    row = await cursor.fetchone()
    if not row:
      raise ValueError(f"Unknown auth provider: {provider}")
    return row[0]
  from server.modules.providers.database.mssql_provider.db_helpers import fetch_json, json_one
  res = await fetch_json(json_one(
    "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (provider,),
  ))
  if not res.rows:
    raise ValueError(f"Unknown auth provider: {provider}")
  return res.rows[0]["recid"]


def unlink_last_provider_v1(args: dict[str, Any]) -> Operation:
  guid = args["guid"]
  provider = args["provider"]
  sql = "EXEC auth_unlink_last_provider @guid=?, @provider=?;"
  return Operation(DbRunMode.EXEC, sql, (guid, provider))
