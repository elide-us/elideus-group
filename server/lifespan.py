from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from server.helpers.logging import configure_root_logging

from server.modules.env_module import EnvironmentModule
from server.modules.storage_module import StorageModule
from server.modules.discord_module import DiscordModule
from server.modules.auth_module import AuthModule
from server.modules.permcap_module import PermCapModule
from server.modules.mssql_module import MSSQLModule

from server.helpers import roles as role_helper

@asynccontextmanager
async def lifespan(app: FastAPI):
  mssql_dsn = os.getenv("AZURE_SQL_CONNECTION_STRING")
  app.state.mssql = MSSQLModule(app, dsn=mssql_dsn)
  await app.state.mssql.startup()

  await role_helper.load_roles(app.state.mssql)

  debug = await app.state.mssql.get_config_value("DebugLogging")
  configure_root_logging(debug=str(debug).lower() in ["1", "true"])

  app.state.env = EnvironmentModule(app)

  app.state.storage = StorageModule(app)
  await app.state.storage.startup()

  app.state.discord = DiscordModule(app)
  await app.state.discord.startup()

  app.state.auth = AuthModule(app)
  await app.state.auth.startup()

  app.state.permcap = PermCapModule(app)
  await app.state.permcap.startup()

  try:
    yield
  finally:
    return

