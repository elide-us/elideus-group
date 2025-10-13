"""MSSQL helpers for OAuth relinking across providers."""

from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from server.registry.providers.mssql import run_exec
from server.registry.types import DBResponse

from server.registry.users.security.identities import mssql as identities_mssql

__all__ = [
  "relink_discord_v1",
  "relink_google_v1",
  "relink_microsoft_v1",
]


async def relink_discord_v1(args: dict[str, Any]) -> DBResponse:
  raw_id = args["provider_identifier"]
  identifier = str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{raw_id}"))))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='discord', @identifier=?, @email=?, @display=?, @image=?;"
  await run_exec(sql, (identifier, email, display, img))
  return await identities_mssql.get_by_provider_identifier_v1({
    "provider": "discord",
    "provider_identifier": identifier,
  })


async def relink_google_v1(args: dict[str, Any]) -> DBResponse:
  identifier = str(UUID(args["provider_identifier"]))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='google', @identifier=?, @email=?, @display=?, @image=?;"
  await run_exec(sql, (identifier, email, display, img))
  return await identities_mssql.get_by_provider_identifier_v1({
    "provider": "google",
    "provider_identifier": identifier,
  })


async def relink_microsoft_v1(args: dict[str, Any]) -> DBResponse:
  identifier = str(UUID(args["provider_identifier"]))
  email = args.get("email")
  display = args.get("display_name")
  img = args.get("profile_image", "")
  sql = "EXEC auth_oauth_relink @provider='microsoft', @identifier=?, @email=?, @display=?, @image=?;"
  await run_exec(sql, (identifier, email, display, img))
  return await identities_mssql.get_by_provider_identifier_v1({
    "provider": "microsoft",
    "provider_identifier": identifier,
  })
