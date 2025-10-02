"""MSSQL helpers for OAuth relinking across providers."""

from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from server.modules.providers.database.mssql_provider.db_helpers import (
  exec_op,
  exec_query,
  fetch_json,
)

from server.registry.security.identities import mssql as identities_mssql

__all__ = [
  "relink_discord_v1",
  "relink_google_v1",
  "relink_microsoft_v1",
]


async def relink_discord_v1(args: dict[str, Any]):
  raw_id = args["provider_identifier"]
  identifier = str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{raw_id}"))))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='discord', @identifier=?, @email=?, @display=?, @image=?;"
  await exec_query(exec_op(sql, (identifier, email, display, img)))
  sel = identities_mssql.get_by_provider_identifier_v1({
    "provider": "discord",
    "provider_identifier": identifier,
  })
  return await fetch_json(sel)


async def relink_google_v1(args: dict[str, Any]):
  identifier = str(UUID(args["provider_identifier"]))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='google', @identifier=?, @email=?, @display=?, @image=?;"
  await exec_query(exec_op(sql, (identifier, email, display, img)))
  sel = identities_mssql.get_by_provider_identifier_v1({
    "provider": "google",
    "provider_identifier": identifier,
  })
  return await fetch_json(sel)


async def relink_microsoft_v1(args: dict[str, Any]):
  identifier = str(UUID(args["provider_identifier"]))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='microsoft', @identifier=?, @email=?, @display=?, @image=?;"
  await exec_query(exec_op(sql, (identifier, email, display, img)))
  sel = identities_mssql.get_by_provider_identifier_v1({
    "provider": "microsoft",
    "provider_identifier": identifier,
  })
  return await fetch_json(sel)
