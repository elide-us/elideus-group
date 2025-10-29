from __future__ import annotations
from fastapi import FastAPI
from server.registry.system.links import NavbarRoutesParams
from server.modules.registry.helpers import (
  get_home_links_request,
  get_navbar_routes_request,
)
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule

class PublicLinksModule(BaseModule):
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

  async def get_home_links(self):
    assert self.db
    res = await self.db.run(get_home_links_request())
    return res.rows

  async def get_navbar_routes(self, role_mask: int):
    assert self.db
    res = await self.db.run(
      get_navbar_routes_request(NavbarRoutesParams(role_mask=role_mask))
    )
    return res.rows
