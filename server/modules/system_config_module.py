from __future__ import annotations
import logging
from fastapi import FastAPI
from queryregistry.system.config.models import ConfigKeyParams, UpsertConfigParams
from queryregistry.system.config import (
  delete_config_request,
  get_configs_request,
  upsert_config_request,
)
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from server.modules.models.system_config import (
  SystemConfigDeleteResult,
  SystemConfigItem,
  SystemConfigList,
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

  async def get_configs(self, user_guid: str, roles: list[str]) -> SystemConfigList:
    logging.debug("[system_config_get_configs_v1] user=%s roles=%s", user_guid, roles)
    res = await self.db.run(get_configs_request())
    items = [
      SystemConfigItem(
        key=row.get("element_key", ""),
        value=row.get("element_value", ""),
      )
      for row in res.rows
    ]
    logging.debug(
      "[system_config_get_configs_v1] returning %d items",
      len(items),
    )
    return SystemConfigList(items=items)

  async def upsert_config(self, user_guid: str, roles: list[str], key: str, value: str) -> SystemConfigItem:
    logging.debug(
      "[system_config_upsert_config_v1] user=%s roles=%s payload={'key': %s, 'value': %s}",
      user_guid,
      roles,
      key,
      value,
    )
    await self.db.run(
      upsert_config_request(UpsertConfigParams(key=key, value=value)),
    )
    logging.debug(
      "[system_config_upsert_config_v1] upserted config %s",
      key,
    )
    return SystemConfigItem(key=key, value=value)

  async def delete_config(self, user_guid: str, roles: list[str], key: str) -> SystemConfigDeleteResult:
    logging.debug(
      "[system_config_delete_config_v1] user=%s roles=%s payload={'key': %s}",
      user_guid,
      roles,
      key,
    )
    await self.db.run(
      delete_config_request(ConfigKeyParams(key=key)),
    )
    logging.debug(
      "[system_config_delete_config_v1] deleted config %s",
      key,
    )
    return SystemConfigDeleteResult(key=key)
