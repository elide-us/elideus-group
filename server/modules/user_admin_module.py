from fastapi import FastAPI, HTTPException
from server.modules import BaseModule
from server.modules.db_module import DbModule
from rpc.users.profile.models import UsersProfileProfile1
import json


class UserAdminModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def get_profile(self, guid: str) -> UsersProfileProfile1:
    res = await self.db.run("db:users:profile:get_profile:1", {"guid": guid})
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")
    row = res.rows[0]
    row["guid"] = str(row.get("guid", ""))
    auth_providers = row.get("auth_providers")
    if isinstance(auth_providers, str):
      row["auth_providers"] = json.loads(auth_providers) if auth_providers else []
    return UsersProfileProfile1(**row)

  async def set_credits(self, guid: str, credits: int) -> None:
    await self.db.run(
      "db:support:users:set_credits:1",
      {"guid": guid, "credits": credits},
    )

  async def reset_display(self, guid: str) -> None:
    await self.db.run(
      "db:users:profile:set_display:1",
      {"guid": guid, "display_name": "Default User"},
    )
