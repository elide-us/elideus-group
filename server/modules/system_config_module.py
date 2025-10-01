from __future__ import annotations
import logging
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from server.registry.system.config import (
  delete_config_request,
  get_configs_request,
  upsert_config_request,
)
from rpc.system.config.models import (
  SystemConfigConfigItem1,
  SystemConfigDeleteConfig1,
  SystemConfigList1,
)

class SystemConfigModule(BaseModule):
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

  async def get_configs(self, user_guid: str, roles: list[str]) -> SystemConfigList1:
    logging.debug("[system_config_get_configs_v1] user=%s roles=%s", user_guid, roles)
    assert self.db, "database module not initialised"
    request = get_configs_request()
    res = await self.db.run(request.op, request.params)
    items = [
      SystemConfigConfigItem1(
        key=row.get("element_key", ""),
        value=row.get("element_value", ""),
      )
      for row in res.rows
    ]
    logging.debug(
      "[system_config_get_configs_v1] returning %d items",
      len(items),
    )
    return SystemConfigList1(items=items)

  async def upsert_config(self, user_guid: str, roles: list[str], key: str, value: str) -> SystemConfigConfigItem1:
    logging.debug(
      "[system_config_upsert_config_v1] user=%s roles=%s payload={'key': %s, 'value': %s}",
      user_guid,
      roles,
      key,
      value,
    )
    assert self.db, "database module not initialised"
    request = upsert_config_request(key, value)
    await self.db.run(request.op, request.params)
    logging.debug(
      "[system_config_upsert_config_v1] upserted config %s",
      key,
    )
    return SystemConfigConfigItem1(key=key, value=value)

  async def delete_config(self, user_guid: str, roles: list[str], key: str) -> SystemConfigDeleteConfig1:
    logging.debug(
      "[system_config_delete_config_v1] user=%s roles=%s payload={'key': %s}",
      user_guid,
      roles,
      key,
    )
    assert self.db, "database module not initialised"
    request = delete_config_request(key)
    await self.db.run(request.op, request.params)
    logging.debug(
      "[system_config_delete_config_v1] deleted config %s",
      key,
    )
    return SystemConfigDeleteConfig1(key=key)
