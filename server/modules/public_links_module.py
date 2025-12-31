from __future__ import annotations
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI
from queryregistry import dispatch_query_request
from queryregistry.models import DBRequest
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule


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
    res = await dispatch_query_request(
      DBRequest(op="db:system:links:get_home_links:1"),
      provider=self.db.provider,
    )
    return _normalize_payload(res.payload)

  async def get_navbar_routes(self, role_mask: int):
    assert self.db
    res = await dispatch_query_request(
      DBRequest(
        op="db:system:links:get_navbar_routes:1",
        payload={"role_mask": role_mask},
      ),
      provider=self.db.provider,
    )
    return _normalize_payload(res.payload)
