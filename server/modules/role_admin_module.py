from fastapi import FastAPI, HTTPException
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule
from server.modules.discord_bot_module import DiscordBotModule
from server.registry.system.roles import (
  add_role_member_request,
  get_role_members_request,
  get_role_non_members_request,
  list_roles_request,
  remove_role_member_request,
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
    assert self.db, "database module not initialised"
    request = list_roles_request()
    res = await self.db.run(request)
    roles = [
      {
        "name": r.get("name", ""),
        "mask": str(r.get("mask", "")),
        "display": r.get("display"),
      }
      for r in res.rows
      if r.get("name") != "ROLE_REGISTERED"
    ]
    roles.sort(key=lambda r: int(r.get("mask", 0)))
    if actor_mask is not None:
      max_mask = self._max_mask(actor_mask)
      roles = [r for r in roles if int(r.get("mask", 0)) <= max_mask]
    return roles

  async def get_role_members(self, role: str) -> tuple[list[dict], list[dict]]:
    assert self.db, "database module not initialised"
    mem_request = get_role_members_request(role)
    mem_res = await self.db.run(mem_request)
    non_request = get_role_non_members_request(role)
    non_res = await self.db.run(non_request)
    members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in mem_res.rows
    ]
    non_members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in non_res.rows
    ]
    return members, non_members

  async def add_role_member(self, role: str, user_guid: str, actor_mask: int | None = None) -> tuple[list[dict], list[dict]]:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    assert self.db, "database module not initialised"
    request = add_role_member_request(role, user_guid)
    await self.db.run(request)
    await self.auth.refresh_user_roles(user_guid)
    return await self.get_role_members(role)

  async def remove_role_member(self, role: str, user_guid: str, actor_mask: int | None = None) -> tuple[list[dict], list[dict]]:
    if actor_mask is not None:
      role_mask = self.auth.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    assert self.db, "database module not initialised"
    request = remove_role_member_request(role, user_guid)
    await self.db.run(request)
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
