from fastapi import FastAPI, HTTPException
from server.modules import BaseModule
from server.modules.db_module import DbModule
from server.modules.discord_bot_module import DiscordBotModule
from server.registry.account.profile.model import GuidParams, SetDisplayParams
from server.registry.finance.credits.model import SetCreditsParams
from server.modules.registry.helpers import (
  get_profile_request,
  set_credits_request,
  set_display_request,
)


class UserAdminModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordBotModule | None = None

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def get_displayname(self, guid: str) -> str:
    params = GuidParams(guid=guid)
    res = await self.db.run(get_profile_request(params))
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")
    row = res.rows[0]
    return row.get("display_name", "")

  async def get_credits(self, guid: str) -> int:
    params = GuidParams(guid=guid)
    res = await self.db.run(get_profile_request(params))
    if not res.rows:
      raise HTTPException(status_code=404, detail="Profile not found")
    row = res.rows[0]
    credits = row.get("credits")
    if credits is None:
      raise HTTPException(status_code=404, detail="Credits not found")
    return credits

  async def set_credits(self, guid: str, credits: int) -> None:
    await self.db.run(
      set_credits_request(SetCreditsParams(guid=guid, credits=credits))
    )

  async def reset_display(self, guid: str) -> None:
    params = SetDisplayParams(guid=guid, display_name="Default User")
    await self.db.run(set_display_request(params))
