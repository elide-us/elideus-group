"""Database module loader."""

import os
from importlib import import_module
from typing import Any, Dict, Protocol, cast, Awaitable, Callable
from pydantic import BaseModel
from fastapi import FastAPI

from . import BaseModule
from .env_module import EnvModule


class DBResult(BaseModel):
  rows: list[dict] = []
  rowcount: int = 0


class Provider(Protocol):
  async def init(**cfg) -> None: ...
  async def dispatch(op: str, args: Dict[str, Any]) -> Dict[str, Any] | DBResult: ...


_exec: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any] | DBResult]] | None = None


async def init(provider: str | None = None, **cfg):
  """Initialize database provider.

  Provider name can be supplied directly, via a ``provider`` key in ``cfg``, or
  from the ``DATABASE_PROVIDER`` environment variable. Defaults to ``mssql``.
  """

  global _exec
  provider_name = provider or cfg.pop("provider", None) or os.getenv("DATABASE_PROVIDER", "mssql")

  try:
    mod = import_module(f".providers.{provider_name}_provider", __package__)
  except ModuleNotFoundError as e:
    raise ValueError(f"Unsupported provider: {provider_name}") from e

  if not hasattr(mod, "init") or not hasattr(mod, "dispatch"):
    raise ValueError(f"Provider '{provider_name}' missing required interface")

  provider_mod = cast(Provider, mod)
  await provider_mod.init(**cfg)
  _exec = provider_mod.dispatch


async def run(op: str, args: Dict[str, Any]) -> DBResult:
  assert _exec, "database_module not initialized"
  out = await _exec(op, args)
  # normalize to DBResult
  if isinstance(out, DBResult):
    return out
  return DBResult(**out)  # expects {"rows":[...], "rowcount":N}


class DatabaseModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()
    provider = env.get("DATABASE_PROVIDER")
    cfg: Dict[str, Any] = {}
    if provider == "mssql":
      cfg["dsn"] = env.get("AZURE_SQL_CONNECTION_STRING")
    elif provider == "postgres":
      cfg["dsn"] = env.get("POSTGRES_CONNECTION_STRING")
    await init(provider=provider, **cfg)
    self.app.state.db = self
    self.app.state.db_provider = provider
    self.mark_ready()

  async def shutdown(self):
    return

  async def run(self, op: str, args: Dict[str, Any]) -> DBResult:
    return await run(op, args)
