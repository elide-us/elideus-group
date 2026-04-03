from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException
from queryregistry.identity.roles import (
  create_role_membership_request,
  delete_role_membership_request,
  list_all_role_memberships_request,
  list_role_memberships_request,
  list_role_non_memberships_request,
)
from queryregistry.identity.roles.models import (
  ModifyRoleMemberParams,
  RoleScopeParams,
)
from queryregistry.system.roles import list_system_roles_request
from rpc.account.role.models import (
  AccountRoleAggregateItem1,
  AccountRoleAggregateList1,
  AccountRoleList1,
  AccountRoleMembers1,
  AccountRoleRoleItem1,
  AccountRoleUserItem1,
)
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.discord_bot_module import DiscordBotModule
from server.modules.role_module import RoleModule


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
    self.role: RoleModule = self.app.state.role
    await self.role.on_ready()
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

  async def list_roles(self, actor_mask: int | None = None) -> AccountRoleList1:
    res = await self.db.run(list_system_roles_request())
    roles = [
      AccountRoleRoleItem1(
        name=r.get("name", ""),
        mask=str(r.get("mask", "")),
        display=r.get("display"),
      )
      for r in _normalize_payload(res.payload)
    ]
    roles.sort(key=lambda r: int(r.mask))
    if actor_mask is not None:
      max_mask = self._max_mask(actor_mask)
      roles = [r for r in roles if int(r.mask) <= max_mask]
    return AccountRoleList1(roles=roles)

  async def get_role_members(self, role: str) -> AccountRoleMembers1:
    scope = RoleScopeParams(role=role)
    mem_res = await self.db.run(list_role_memberships_request(scope))
    non_res = await self.db.run(list_role_non_memberships_request(scope))
    members = [
      AccountRoleUserItem1(
        guid=r.get("guid", ""),
        displayName=r.get("display_name", ""),
      )
      for r in _normalize_payload(mem_res.payload)
    ]
    non_members = [
      AccountRoleUserItem1(
        guid=r.get("guid", ""),
        displayName=r.get("display_name", ""),
      )
      for r in _normalize_payload(non_res.payload)
    ]
    return AccountRoleMembers1(members=members, nonMembers=non_members)

  async def get_all_role_members(self, actor_mask: int | None = None) -> AccountRoleAggregateList1:
    """Return all roles with members and non-members in a single query."""
    res = await self.db.run(list_all_role_memberships_request())
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
        AccountRoleAggregateItem1(
          name=r.get("name", ""),
          mask=str(mask_val),
          display=r.get("display"),
          members=[
            AccountRoleUserItem1(
              guid=m.get("guid", ""),
              displayName=m.get("display_name", ""),
            )
            for m in members_raw
          ],
          nonMembers=[
            AccountRoleUserItem1(
              guid=m.get("guid", ""),
              displayName=m.get("display_name", ""),
            )
            for m in non_members_raw
          ],
        )
      )
    roles.sort(key=lambda r: int(r.mask))
    return AccountRoleAggregateList1(roles=roles)

  async def add_role_member(
    self,
    role: str,
    user_guid: str,
    actor_mask: int | None = None,
  ) -> AccountRoleMembers1:
    if actor_mask is not None:
      role_mask = self.role.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    payload = ModifyRoleMemberParams(role=role, user_guid=user_guid)
    await self.db.run(create_role_membership_request(payload))
    await self.role.refresh_user_roles(user_guid)
    return await self.get_role_members(role)

  async def remove_role_member(
    self,
    role: str,
    user_guid: str,
    actor_mask: int | None = None,
  ) -> AccountRoleMembers1:
    if actor_mask is not None:
      role_mask = self.role.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    payload = ModifyRoleMemberParams(role=role, user_guid=user_guid)
    await self.db.run(delete_role_membership_request(payload))
    await self.role.refresh_user_roles(user_guid)
    return await self.get_role_members(role)

  async def upsert_role(
    self,
    name: str,
    mask: str,
    display: str | None,
    actor_mask: int | None = None,
  ) -> None:
    role_mask = int(mask)
    if actor_mask is not None:
      self._ensure_can_manage(actor_mask, role_mask)
    await self.role.upsert_role(name, role_mask, display)

  async def delete_role(self, name: str, actor_mask: int | None = None) -> None:
    if actor_mask is not None:
      role_mask = self.role.roles.get(name, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    await self.role.delete_role(name)
