from __future__ import annotations

from fastapi import FastAPI

from . import BaseModule
from .env_module import EnvModule


class DatabaseModule(BaseModule):
  """Selects and initializes the configured database provider."""

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.provider = None

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()

    name = env.get("DB_PROVIDER", "mssql").lower()
    if name == "postgresql":
      from .providers.postgres_provider import PostgreSQLProvider
      self.provider = PostgreSQLProvider()
    else:
      from .providers.mssql_provider import MSSQLProvider
      self.provider = MSSQLProvider()

    if hasattr(self.provider, "startup"):
      await self.provider.startup()
    self.mark_ready()

  async def shutdown(self):
    if self.provider and hasattr(self.provider, "shutdown"):
      await self.provider.shutdown()
    self.provider = None

  async def execute(self, query: str, *args, **kwargs):
    if not self.provider:
      raise RuntimeError("Database provider not initialized")
    return await self.provider.execute(query, *args, **kwargs)

  async def fetch_one(self, query: str, *args, **kwargs):
    if not self.provider:
      raise RuntimeError("Database provider not initialized")
    return await self.provider.fetch_one(query, *args, **kwargs)

  async def fetch_many(self, query: str, *args, **kwargs):
    if not self.provider:
      raise RuntimeError("Database provider not initialized")
    return await self.provider.fetch_many(query, *args, **kwargs)
