from __future__ import annotations
import logging
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule
from .discord_module import DiscordModule
from rpc.system.config.models import (
  SystemConfigConfigItem1,
  SystemConfigDeleteConfig1,
  SystemConfigList1,
)

class SystemConfigModule(BaseModule):
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

  async def get_configs(self, user_guid: str, roles: list[str]) -> SystemConfigList1:
    logging.debug("[system_config_get_configs_v1] user=%s roles=%s", user_guid, roles)
    res = await self.db.run("db:system:config:get_configs:1", {})
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
    await self.db.run(
      "db:system:config:upsert_config:1",
      {"key": key, "value": value},
    )
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
    await self.db.run(
      "db:system:config:delete_config:1",
      {"key": key},
    )
    logging.debug(
      "[system_config_delete_config_v1] deleted config %s",
      key,
    )
    return SystemConfigDeleteConfig1(key=key)
