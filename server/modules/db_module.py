"""Database module loader."""

from importlib import import_module
from typing import Any, Dict
import inspect
from fastapi import FastAPI
import logging

from . import BaseModule
from .env_module import EnvModule
from .providers import DbProviderBase
from .providers import DBRequest, DBResponse
from server.registry.users.content.cache import (
  delete_cache_folder_request,
  delete_cache_item_request,
  list_cache_request,
  replace_user_cache_request,
  upsert_cache_item_request,
)
from server.helpers.logging import update_logging_level


class DbModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.provider: str = "mssql"
    self.logging_level: int = 0
    self._provider: DbProviderBase | None = None

  async def init(self, provider: str | None = None, **cfg):
    """Initialize database provider.

    Provider name can be supplied directly, via a ``provider`` key in ``cfg``, or
    from the ``DATABASE_PROVIDER`` environment variable. Defaults to ``mssql``.
    """

    provider_name = provider or "mssql"

    try:
      module = import_module(f".providers.database.{provider_name}_provider", __package__)
    except ModuleNotFoundError as e:
      raise ValueError(f"Unsupported provider: {provider_name}") from e

    provider_cls = None
    for attr in module.__dict__.values():
      if inspect.isclass(attr) and attr.__name__ != "DbProviderBase":
        bases = inspect.getmro(attr)
        if any(b.__name__ == "DbProviderBase" for b in bases) and not inspect.isabstract(attr):
          provider_cls = attr
          break
    if not provider_cls:
      raise ValueError(f"Provider '{provider_name}' missing DbProviderBase implementation")

    self._provider = provider_cls(**cfg)

  async def run(
    self,
    request: DBRequest | str,
    args: Dict[str, Any] | None = None,
  ) -> DBResponse:
    assert self._provider, "db_module not initialized"
    if isinstance(request, str):
      request = DBRequest(op=request, payload=args or {})
    elif args is not None:
      raise TypeError("args cannot be provided when passing a DBRequest instance")
    op = request.op
    out = await self._provider.run(request)
    if isinstance(out, DBResponse):
      if not out.op:
        out.attach_op(op)
      return out
    if isinstance(out, dict):
      rows = out.get("rows")
      rowcount = out.get("rowcount")
      payload = out.get("payload", rows)
      return DBResponse(op=op, payload=payload, rowcount=rowcount)
    raise TypeError(f"Unexpected database response type: {type(out)!r}")

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()
    self.provider = env.get("DATABASE_PROVIDER")
    cfg: Dict[str, Any] = {}
    if self.provider == "mssql":
      cfg = {"dsn": env.get("AZURE_SQL_CONNECTION_STRING")}
    await self.init(provider=self.provider, **cfg)
    assert self._provider
    await self._provider.startup()
    res = await self.run(
      DBRequest(op="db:system:config:get_config:1", payload={"key": "LoggingLevel"})
    )
    val = res.rows[0]["value"] if res.rows else "0"
    try:
      self.logging_level = int(val)
    except ValueError:
      self.logging_level = 0
    update_logging_level(self.logging_level)
    self.mark_ready()

  async def shutdown(self):
    if self._provider:
      await self._provider.shutdown()
      self._provider = None

  async def get_ms_api_id(self) -> str:
    res = await self.run(
      DBRequest(op="db:system:config:get_config:1", payload={"key": "MsApiId"})
    )
    if not res.rows:
      raise ValueError("Missing config value for key: MsApiId")
    return res.rows[0]["value"]

  async def get_google_client_id(self) -> str:
    res = await self.run(
      DBRequest(op="db:system:config:get_config:1", payload={"key": "GoogleClientId"})
    )
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] GoogleClientId=%s", value)
    if not value:
      raise ValueError("Missing config value for key: GoogleClientId")
    return value

  async def get_google_api_secret(self) -> str:
    # Refactored: read Google OAuth client secret from environment
    env: EnvModule = self.app.state.env
    value = env.get("GOOGLE_AUTH_SECRET")
    logging.debug("[DbModule] GoogleAuthSecret loaded: %s", bool(value))
    if not value:
      raise ValueError("Missing env value for key: GOOGLE_AUTH_SECRET")
    return value

  async def get_discord_client_id(self) -> str:
    res = await self.run(
      DBRequest(op="db:system:config:get_config:1", payload={"key": "DiscordClientId"})
    )
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] DiscordClientId=%s", value)
    if not value:
      raise ValueError("Missing config value for key: DiscordClientId")
    return value

  async def get_auth_providers(self) -> list[str]:
    res = await self.run(
      DBRequest(op="db:system:config:get_config:1", payload={"key": "AuthProviders"})
    )
    value = res.rows[0]["value"] if res.rows else None
    if value is None:
      raise ValueError("Missing config value for key: AuthProviders")
    return [p.strip() for p in value.split(',') if p.strip()]

  async def get_jwks_cache_time(self) -> int:
    res = await self.run(
      DBRequest(op="db:system:config:get_config:1", payload={"key": "JwksCacheTime"})
    )
    value = res.rows[0]["value"] if res.rows else None
    if value is None:
      raise ValueError("Missing config value for key: JwksCacheTime")
    return int(value)

  async def list_storage_cache(self, user_guid: str) -> list[Dict[str, Any]]:
    res = await self.run(list_cache_request(user_guid))
    return res.rows

  async def replace_storage_cache(self, user_guid: str, items: list[Dict[str, Any]]):
    await self.run(replace_user_cache_request(user_guid, items))

  async def user_exists(self, user_guid: str) -> bool:
    res = await self.run(
      DBRequest(op="db:users:account:exists:1", payload={"user_guid": user_guid})
    )
    return bool(res.rows)

  async def upsert_storage_cache(self, item: Dict[str, Any]) -> DBResponse:
    return await self.run(upsert_cache_item_request(item))

  async def delete_storage_cache(self, user_guid: str, path: str, filename: str):
    await self.run(delete_cache_item_request(user_guid, path, filename))

  async def delete_storage_cache_folder(self, user_guid: str, path: str):
    await self.run(delete_cache_folder_request(user_guid, path))

