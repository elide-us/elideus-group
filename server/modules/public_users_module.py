from __future__ import annotations
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from server.registry.public.users import (
  get_profile_request,
  get_published_files_request,
)

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
    request = get_profile_request(guid=guid)
    res = await self.db.run(request.op, request.params)
    return res.rows[0] if res.rows else None

  async def get_published_files(self, guid: str):
    assert self.db
    request = get_published_files_request(guid=guid)
    res = await self.db.run(request.op, request.params)
    return res.rows
