"""Database module loader."""

from importlib import import_module
from typing import Any, Dict
import inspect
from fastapi import FastAPI
import logging

from . import BaseModule
from .env_module import EnvModule
from .providers import DbProviderBase
from .providers import DBResult
from server.registry import RegistryDispatcher
from server.registry.types import DBRequest, DBResponse
from server.helpers.logging import update_logging_level


def _current_dbresult_cls():
  from server.modules.providers import DBResult as ProvidersDBResult
  return ProvidersDBResult
class DbModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.provider: str = "mssql"
    self.logging_level: int = 0
    self._provider: DbProviderBase | None = None
    self._registry: RegistryDispatcher | None = getattr(app.state, "registry", None)

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

  def set_registry(self, registry: RegistryDispatcher) -> None:
    self._registry = registry

  async def run(self, op: str | DBRequest, args: Dict[str, Any] | None = None) -> DBResult:
    assert self._provider, "db_module not initialized"
    if not self._registry:
      raise RuntimeError("registry dispatcher not configured")
    if isinstance(op, DBRequest):
      if args is not None:
        raise ValueError("Arguments are not supported when passing a DBRequest")
      request = op
    else:
      request = DBRequest(op=op, params=args or {})
    response = await self._registry.execute(request)
    DBResultCls = _current_dbresult_cls()
    if isinstance(response, DBResponse):
      return response.to_result()
    if isinstance(response, DBResultCls):
      return response
    payload = response.model_dump() if hasattr(response, "model_dump") else response
    return DBResultCls(**payload)

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
    if self._registry:
      self._registry.bind_provider(self._provider)
    res = await self.run("db:system:config:get_config:1", {"key": "LoggingLevel"})
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
    res = await self.run("db:system:config:get_config:1", {"key": "MsApiId"})
    if not res.rows:
      raise ValueError("Missing config value for key: MsApiId")
    return res.rows[0]["value"]

  async def get_google_client_id(self) -> str:
    res = await self.run("db:system:config:get_config:1", {"key": "GoogleClientId"})
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
    res = await self.run("db:system:config:get_config:1", {"key": "DiscordClientId"})
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] DiscordClientId=%s", value)
    if not value:
      raise ValueError("Missing config value for key: DiscordClientId")
    return value

  async def get_auth_providers(self) -> list[str]:
    res = await self.run("db:system:config:get_config:1", {"key": "AuthProviders"})
    value = res.rows[0]["value"] if res.rows else None
    if value is None:
      raise ValueError("Missing config value for key: AuthProviders")
    return [p.strip() for p in value.split(',') if p.strip()]

  async def get_jwks_cache_time(self) -> int:
    res = await self.run("db:system:config:get_config:1", {"key": "JwksCacheTime"})
    value = res.rows[0]["value"] if res.rows else None
    if value is None:
      raise ValueError("Missing config value for key: JwksCacheTime")
    return int(value)

  async def user_exists(self, user_guid: str) -> bool:
    res = await self.run("db:users:account:exists:1", {"user_guid": user_guid})
    return bool(res.rows)

