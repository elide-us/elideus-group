from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule

class PublicGalleryModule(BaseModule):
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

  async def list_public_files(self):
    assert self.db
    res = await self.db.run("db:public:gallery:get_public_files:1", {})
    return res.rows
