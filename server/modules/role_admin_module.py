from fastapi import FastAPI
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.auth_module import AuthModule


class RoleAdminModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def list_roles(self) -> list[dict]:
    res = await self.db.run("db:system:roles:list:1", {})
    return [
      {
        "name": r.get("name", ""),
        "mask": str(r.get("mask", "")),
        "display": r.get("display"),
      }
      for r in res.rows
      if r.get("name") != "ROLE_REGISTERED"
    ]

  async def get_role_members(self, role: str) -> tuple[list[dict], list[dict]]:
    mem_res = await self.db.run("db:security:roles:get_role_members:1", {"role": role})
    non_res = await self.db.run("db:security:roles:get_role_non_members:1", {"role": role})
    members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in mem_res.rows
    ]
    non_members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in non_res.rows
    ]
    return members, non_members

  async def add_role_member(self, role: str, user_guid: str) -> tuple[list[dict], list[dict]]:
    await self.db.run(
      "db:security:roles:add_role_member:1",
      {"role": role, "user_guid": user_guid},
    )
    return await self.get_role_members(role)

  async def remove_role_member(self, role: str, user_guid: str) -> tuple[list[dict], list[dict]]:
    await self.db.run(
      "db:security:roles:remove_role_member:1",
      {"role": role, "user_guid": user_guid},
    )
    return await self.get_role_members(role)

  async def upsert_role(self, name: str, mask: int, display: str | None) -> None:
    await self.auth.upsert_role(name, mask, display)

  async def delete_role(self, name: str) -> None:
    await self.auth.delete_role(name)
