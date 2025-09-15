from fastapi import FastAPI, HTTPException
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.discord_module import DiscordModule


class UserAdminModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordModule | None = None

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def get_displayname(self, guid: str) -> str:
    res = await self.db.run("db:users:profile:get_profile:1", {"guid": guid})
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")
    row = res.rows[0]
    return row.get("display_name", "")

  async def get_credits(self, guid: str) -> int:
    res = await self.db.run("db:users:profile:get_profile:1", {"guid": guid})
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")
    row = res.rows[0]
    credits = row.get("credits")
    if credits is None:
      raise HTTPException(status_code=404, detail="Credits not found")
    return credits

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
