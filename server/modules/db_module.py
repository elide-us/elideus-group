"""Database module loader."""

from importlib import import_module
from typing import Any, Dict, cast, Awaitable, Callable
from fastapi import FastAPI
import logging

from . import BaseModule
from .env_module import EnvModule
from .providers import Provider
from .providers.models import DBResult
from server.helpers.logging import update_logging_level


_dispatch_executor: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any] | DBResult]] | None = None
_shutdown_executor: Callable[[], Awaitable[None]] | None = None


async def init(provider: str | None = None, **cfg):
  """Initialize database provider.

  Provider name can be supplied directly, via a ``provider`` key in ``cfg``, or
  from the ``DATABASE_PROVIDER`` environment variable. Defaults to ``mssql``.
  """

  global _dispatch_executor, _shutdown_executor
  provider_name = provider or "mssql"

  try:
    _module = import_module(f".providers.{provider_name}_provider", __package__)
  except ModuleNotFoundError as e:
    raise ValueError(f"Unsupported provider: {provider_name}") from e

  if not hasattr(_module, "init") or not hasattr(_module, "dispatch"):
    raise ValueError(f"Provider '{provider_name}' missing required interface")

  provider_mod = cast(Provider, _module)
  await provider_mod.init(**cfg)
  _dispatch_executor = provider_mod.dispatch
  _shutdown_executor = getattr(provider_mod, "close_pool", None)


async def run(op: str, args: Dict[str, Any]) -> DBResult:
  assert _dispatch_executor, "db_module not initialized"
  out = await _dispatch_executor(op, args)
  # normalize to DBResult
  if isinstance(out, DBResult):
    return out
  return DBResult(**out)  # expects {"rows":[...], "rowcount":N}


class DbModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.provider: str = "mssql"
    self.debug_logging: bool = False

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()
    self.provider = env.get("DATABASE_PROVIDER")
    cfg: Dict[str, Any] = {}
    if self.provider == "mssql":
      cfg = {"dsn": env.get("AZURE_SQL_CONNECTION_STRING")}
    await init(provider=self.provider, **cfg)
    res = await run("db:system:config:get_config:1", {"key": "DebugLogging"})
    val = res.rows[0]["value"] if res.rows else ""
    self.debug_logging = str(val).lower() == "true"
    update_logging_level(self.debug_logging)
    self.mark_ready()

  async def shutdown(self):
    global _shutdown_executor
    if _shutdown_executor:
      await _shutdown_executor()
      _shutdown_executor = None

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    return await run(op, args)

  async def get_ms_api_id(self) -> str:
    res = await self.run("db:system:config:get_config:1", {"key": "MsApiId"})
    if not res.rows:
      raise ValueError("Missing config value for key: MsApiId")
    return res.rows[0]["value"]

  async def get_google_api_id(self) -> str:
    res = await self.run("db:system:config:get_config:1", {"key": "GoogleApiId"})
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] GoogleApiId=%s", value)
    if not value:
      raise ValueError("Missing config value for key: GoogleApiId")
    return value

  async def get_google_api_secret(self) -> str:
    res = await self.run("db:system:config:get_config:1", {"key": "GoogleApiSecret"})
    value = res.rows[0]["value"] if res.rows else None
    logging.debug("[DbModule] GoogleApiSecret=%s", value)
    if not value:
      raise ValueError("Missing config value for key: GoogleApiSecret")
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
