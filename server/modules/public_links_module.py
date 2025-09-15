from __future__ import annotations
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_module import DiscordModule

class PublicLinksModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.discord: DiscordModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def get_home_links(self):
    res = await self.db.run("db:public:links:get_home_links:1", {})
    return res.rows

  async def get_navbar_routes(self, role_mask: int):
    res = await self.db.run("db:public:links:get_navbar_routes:1", {"role_mask": role_mask})
    return res.rows
