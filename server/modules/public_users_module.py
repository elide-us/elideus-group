from __future__ import annotations
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule

class PublicUsersModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.discord: DiscordBotModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def get_profile(self, guid: str):
    assert self.db
    res = await self.db.run("db:public:users:get_profile:1", {"guid": guid})
    return res.rows[0] if res.rows else None

  async def get_published_files(self, guid: str):
    assert self.db
    res = await self.db.run("db:public:users:get_published_files:1", {"guid": guid})
    return res.rows
