from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException
from queryregistry.handler import dispatch_query_request
from queryregistry.identity.role_memberships import (
  create_role_membership_request,
  delete_role_membership_request,
  list_all_role_memberships_request,
  list_role_memberships_request,
  list_role_non_memberships_request,
)
from queryregistry.identity.role_memberships.models import (
  ModifyRoleMemberParams,
  RoleScopeParams,
)
from queryregistry.system.roles import list_system_roles_request
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from server.modules.discord_bot_module import DiscordBotModule


def _normalize_payload(payload: Any | None) -> list[dict[str, Any]]:
  if payload is None:
    return []
  if isinstance(payload, list):
    return [dict(item) for item in payload]
  if isinstance(payload, Mapping):
    return [dict(payload)]
  return [dict(payload)]


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
    res = await dispatch_query_request(
      list_system_roles_request(),
      provider=self.db.provider or "mssql",
    )
    roles = [
      {
        "name": r.get("name", ""),
        "mask": str(r.get("mask", "")),
        "display": r.get("display"),
      }
      for r in _normalize_payload(res.payload)
    ]
    roles.sort(key=lambda r: int(r.get("mask", 0)))
    if actor_mask is not None:
      max_mask = self._max_mask(actor_mask)
      roles = [r for r in roles if int(r.get("mask", 0)) <= max_mask]
    return roles

  async def get_role_members(self, role: str) -> tuple[list[dict], list[dict]]:
    provider_name = self.db.provider or "mssql"
    scope = RoleScopeParams(role=role)
    mem_res = await dispatch_query_request(
      list_role_memberships_request(scope),
      provider=provider_name,
    )
    non_res = await dispatch_query_request(
      list_role_non_memberships_request(scope),
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

  async def get_all_role_members(self, actor_mask: int | None = None) -> list[dict]:
    """Return all roles with members and non-members in a single query."""
    provider_name = self.db.provider or "mssql"
    res = await dispatch_query_request(
      list_all_role_memberships_request(),
      provider=provider_name,
    )
    roles = []
    for r in _normalize_payload(res.payload):
      mask_val = int(r.get("mask", 0))
      if actor_mask is not None:
        max_mask = self._max_mask(actor_mask)
        if mask_val > max_mask:
          continue
      members_raw = r.get("members") or []
      non_members_raw = r.get("non_members") or []
      roles.append(
        {
          "name": r.get("name", ""),
          "mask": str(mask_val),
          "display": r.get("display"),
          "members": [
            {"guid": m.get("guid", ""), "displayName": m.get("display_name", "")}
            for m in members_raw
          ],
          "nonMembers": [
            {"guid": m.get("guid", ""), "displayName": m.get("display_name", "")}
            for m in non_members_raw
          ],
        }
      )
    roles.sort(key=lambda r: int(r.get("mask", 0)))
    return roles

  async def add_role_member(self, role: str, user_guid: str, actor_mask: int | None = None) -> tuple[list[dict], list[dict]]:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    provider_name = self.db.provider or "mssql"
    payload = ModifyRoleMemberParams(role=role, user_guid=user_guid)
    await dispatch_query_request(
      create_role_membership_request(payload),
      provider=provider_name,
    )
    await self.auth.refresh_user_roles(user_guid)
    return await self.get_role_members(role)

  async def remove_role_member(self, role: str, user_guid: str, actor_mask: int | None = None) -> tuple[list[dict], list[dict]]:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    provider_name = self.db.provider or "mssql"
    payload = ModifyRoleMemberParams(role=role, user_guid=user_guid)
    await dispatch_query_request(
      delete_role_membership_request(payload),
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
