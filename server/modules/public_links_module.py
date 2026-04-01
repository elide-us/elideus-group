from __future__ import annotations
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from queryregistry.system.public import (
  get_home_links_request,
  get_navbar_routes_request,
)


def _normalize_payload(payload: Any | None) -> list[dict[str, Any]]:
  if payload is None:
    return []
  if isinstance(payload, list):
    return [dict(item) for item in payload]
  if isinstance(payload, Mapping):
    return [dict(payload)]
  return [dict(payload)]


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
    return _normalize_payload(res.rows)

  async def get_navbar_routes(self, role_mask: int):
    assert self.db
    res = await self.db.run(get_navbar_routes_request(role_mask))
    return _normalize_payload(res.rows)
