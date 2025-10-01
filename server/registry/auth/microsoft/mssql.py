"""MSSQL helpers for Microsoft OAuth relinking."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.modules.providers.database.mssql_provider.db_helpers import (
  exec_op,
  exec_query,
  fetch_json,
)

from server.registry.users.providers import mssql as users_providers

__all__ = [
  "oauth_relink_v1",
]


async def oauth_relink_v1(args: dict[str, Any]):
  identifier = str(UUID(args["provider_identifier"]))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='microsoft', @identifier=?, @email=?, @display=?, @image=?;"
  await exec_query(exec_op(sql, (identifier, email, display, img)))
  sel = users_providers.get_by_provider_identifier_v1({
    "provider": "microsoft",
    "provider_identifier": identifier,
  })
  return await fetch_json(sel)
