"""Database CLI module exposing management helpers."""

from fastapi import FastAPI
import logging
from . import BaseModule
from .env_module import EnvModule
from .database_cli import mssql_cli


class DatabaseCliModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._dsn: str | None = None

  async def startup(self):
    env: EnvModule = self.app.state.env
    await env.on_ready()
    self._dsn = env.get("AZURE_SQL_CONNECTION_STRING")
    if not self._dsn:
      logging.error("[DatabaseCli] Missing AZURE_SQL_CONNECTION_STRING")
      raise RuntimeError("AZURE_SQL_CONNECTION_STRING not configured")
    logging.info("[DatabaseCli] module ready")
    self.mark_ready()

  async def shutdown(self):
    self._dsn = None

  async def connect(self, dbname: str | None = None):
    await self.on_ready()
    return await mssql_cli.connect(dsn=self._dsn, dbname=dbname)

  async def reconnect(self, conn, dbname: str):
    await self.on_ready()
    return await mssql_cli.reconnect(conn, dsn=self._dsn, dbname=dbname)

  async def list_tables(self, conn):
    await self.on_ready()
    return await mssql_cli.list_tables(conn)
