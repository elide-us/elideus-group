from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException
from queryregistry.handler import dispatch_query_request
from queryregistry.models import DBResponse
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from server.modules.discord_bot_module import DiscordBotModule
from server.registry.models import DBRequest
from server.registry.system.roles.model import (
  ModifyRoleMemberParams,
  RoleScopeParams,
)
from server.modules.registry.helpers import (
  create_role_membership_request,
  dispatch_query_request_with_fallback,
  delete_role_membership_request,
  list_role_memberships_request,
  list_role_non_memberships_request,
  list_system_roles_request,
)


def _normalize_payload(payload: Any | None) -> list[dict[str, Any]]:
  if payload is None:
    return []
  if isinstance(payload, list):
    return [dict(item) for item in payload]
  if isinstance(payload, Mapping):
    return [dict(payload)]
  return [dict(payload)]


async def _dispatch_role_request(
  db: DbModule,
  request,
  *,
  fallback_op: str,
) -> DBResponse:
  provider_name = db.provider or "mssql"

  async def fallback() -> DBResponse:
    legacy_response = await db.run(
      DBRequest(op=fallback_op, payload=request.payload),
    )
    return DBResponse(op=request.op, payload=legacy_response.payload)

  return await dispatch_query_request_with_fallback(
    request,
    provider=provider_name,
    fallback=fallback,
  )


class RoleAdminModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordBotModule | None = None

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  def _max_mask(self, mask: int) -> int:
    if mask == 0:
      return 0
    return 1 << (mask.bit_length() - 1)

  def _ensure_can_manage(self, actor_mask: int, target_mask: int) -> None:
    max_mask = self._max_mask(actor_mask)
    if target_mask > max_mask:
      raise HTTPException(status_code=403, detail="Forbidden")

  async def list_roles(self, actor_mask: int | None = None) -> list[dict]:
    res = await _dispatch_role_request(
      self.db,
      list_system_roles_request(),
      fallback_op="db:system:roles:list:1",
    )
    roles = [
      {
        "name": r.get("name", ""),
        "mask": str(r.get("mask", "")),
        "display": r.get("display"),
      }
      for r in _normalize_payload(res.payload)
      if r.get("name") != "ROLE_REGISTERED"
    ]
    roles.sort(key=lambda r: int(r.get("mask", 0)))
    if actor_mask is not None:
      max_mask = self._max_mask(actor_mask)
      roles = [r for r in roles if int(r.get("mask", 0)) <= max_mask]
    return roles

  async def get_role_members(self, role: str) -> tuple[list[dict], list[dict]]:
    provider_name = self.db.provider or "mssql"
    mem_res = await dispatch_query_request(
      list_role_memberships_request(RoleScopeParams(role=role)),
      provider=provider_name,
    )
    non_res = await dispatch_query_request(
      list_role_non_memberships_request(RoleScopeParams(role=role)),
      provider=provider_name,
    )
    members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in _normalize_payload(mem_res.payload)
    ]
    non_members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in _normalize_payload(non_res.payload)
    ]
    return members, non_members

  async def add_role_member(self, role: str, user_guid: str, actor_mask: int | None = None) -> tuple[list[dict], list[dict]]:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    provider_name = self.db.provider or "mssql"
    await dispatch_query_request(
      create_role_membership_request(ModifyRoleMemberParams(role=role, user_guid=user_guid)),
      provider=provider_name,
    )
    await self.auth.refresh_user_roles(user_guid)
    return await self.get_role_members(role)

  async def remove_role_member(self, role: str, user_guid: str, actor_mask: int | None = None) -> tuple[list[dict], list[dict]]:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    provider_name = self.db.provider or "mssql"
    await dispatch_query_request(
      delete_role_membership_request(ModifyRoleMemberParams(role=role, user_guid=user_guid)),
      provider=provider_name,
    )
    await self.auth.refresh_user_roles(user_guid)
    return await self.get_role_members(role)

  async def upsert_role(self, name: str, mask: int, display: str | None, actor_mask: int | None = None) -> None:
    if actor_mask is not None:
      self._ensure_can_manage(actor_mask, mask)
    await self.auth.upsert_role(name, mask, display)

  async def delete_role(self, name: str, actor_mask: int | None = None) -> None:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(name, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    await self.auth.delete_role(name)
