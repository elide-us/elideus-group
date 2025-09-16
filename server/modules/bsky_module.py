from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass

from atproto import AsyncClient as AsyncBskyClient, client_utils
from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule


@dataclass
class BskyPostResult:
  uri: str
  cid: str
  handle: str
  display_name: str | None = None


class BskyModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._handle: str = "elideusgroup.com"
    self._password: str | None = None
    self._client_factory = AsyncBskyClient

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self._handle = await self._load_optional_config("BskyHandle") or self._handle
    self._password = await self._load_optional_config("BskyPassword") or None
    if not self._password:
      logging.warning("[BskyModule] Missing config value for key: BskyPassword")
    self.mark_ready()

  async def shutdown(self):
    self.db = None
    self._password = None

  async def _load_optional_config(self, key: str) -> str:
    if not self.db:
      raise RuntimeError("BskyModule requires database module")
    res = await self.db.run("db:system:config:get_config:1", {"key": key})
    if not res.rows:
      return ""
    return res.rows[0].get("value") or ""

  async def _ensure_credentials(self):
    if not self.db:
      raise RuntimeError("BskyModule requires database module")
    if not self._password:
      self._password = await self._load_optional_config("BskyPassword") or None
    if not self._password:
      raise ValueError("Missing config value for key: BskyPassword")
    if not self._handle:
      self._handle = await self._load_optional_config("BskyHandle") or ""
    if not self._handle:
      raise ValueError("Missing config value for key: BskyHandle")

  @asynccontextmanager
  async def _client_session(self):
    await self._ensure_credentials()
    client = self._client_factory()
    try:
      profile = await client.login(self._handle, self._password)
      yield client, profile
    finally:
      try:
        await client.request.close()
      except Exception:  # pragma: no cover - close failures should not break flow
        logging.exception("[BskyModule] Failed to close Bluesky client session")

  async def post_message(self, message: str) -> BskyPostResult:
    if not message or not message.strip():
      raise ValueError("Message must not be empty")
    async with self._client_session() as (client, profile):
      text = client_utils.TextBuilder().text(message)
      record = await client.send_post(text)
      display_name = getattr(profile, "display_name", None)
      handle = getattr(profile, "handle", self._handle)
      return BskyPostResult(
        uri=record.uri,
        cid=record.cid,
        handle=handle,
        display_name=display_name,
      )
