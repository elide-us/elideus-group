"""Database module loader."""

from importlib import import_module
from typing import Any, Dict
import inspect
from fastapi import FastAPI
import logging

from . import BaseModule
from .env_module import EnvModule
from .providers import DbProviderBase
from .providers.models import DBResult
from server.helpers.logging import update_logging_level


class DbModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.provider: str = "mssql"
    self.debug_logging: bool = False
    self._provider: DbProviderBase | None = None

  async def init(self, provider: str | None = None, **cfg):
    """Initialize database provider.

    Provider name can be supplied directly, via a ``provider`` key in ``cfg``, or
    from the ``DATABASE_PROVIDER`` environment variable. Defaults to ``mssql``.
    """

    provider_name = provider or "mssql"

    try:
      module = import_module(f".providers.{provider_name}_provider", __package__)
    except ModuleNotFoundError as e:
      raise ValueError(f"Unsupported provider: {provider_name}") from e

    provider_cls = None
    for attr in module.__dict__.values():
      if (
        inspect.isclass(attr)
        and issubclass(attr, DbProviderBase)
        and attr is not DbProviderBase
        and not inspect.isabstract(attr)
      ):
        provider_cls = attr
        break
    if not provider_cls:
      raise ValueError(f"Provider '{provider_name}' missing DbProviderBase implementation")

    self._provider = provider_cls(**cfg)

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    assert self._provider, "db_module not initialized"
    out = await self._provider.run(op, args)
    # normalize to DBResult
    if isinstance(out, DBResult):
      return out
    return DBResult(**out)  # expects {"rows":[...], "rowcount":N}

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
    res = await self.run("db:system:config:get_config:1", {"key": "DebugLogging"})
    val = res.rows[0]["value"] if res.rows else ""
    self.debug_logging = str(val).lower() == "true"
    update_logging_level(self.debug_logging)
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

  async def get_google_api_id(self) -> str:
    res = await self.run("db:system:config:get_config:1", {"key": "GoogleApiId"})
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] GoogleApiId=%s", value)
    if not value:
      raise ValueError("Missing config value for key: GoogleApiId")
    return value

  async def get_google_api_secret(self) -> str:
    # Note: legacy naming stores the Google OAuth client secret under
    # the "GoogleApiId" key in system_config.
    res = await self.run("db:system:config:get_config:1", {"key": "GoogleApiId"})
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] GoogleApiSecret=%s", value)
    if not value:
      raise ValueError("Missing config value for key: GoogleApiId")
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

