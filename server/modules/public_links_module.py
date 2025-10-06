from __future__ import annotations
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from server.registry.content.public.links import (
  get_home_links_request,
  get_navbar_routes_request,
)

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
    request = get_home_links_request()
    res = await self.db.run(request)
    return res.rows

  async def get_navbar_routes(self, role_mask: int):
    assert self.db
    request = get_navbar_routes_request(role_mask=role_mask)
    res = await self.db.run(request)
    return res.rows
