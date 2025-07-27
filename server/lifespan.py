from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from server.helpers.logging import configure_root_logging

from server.modules.database_module import DatabaseModule
from server.modules.env_module import EnvironmentModule
from server.modules.storage_module import StorageModule
from server.modules.discord_module import DiscordModule
from server.modules.auth_module import AuthModule
from server.modules.permcap_module import PermCapModule
from server.modules.mssql_module import MSSQLModule

from server.helpers import roles as role_helper

@asynccontextmanager
async def lifespan(app: FastAPI):
  dsn = os.getenv("POSTGRES_CONNECTION_STRING")
  app.state.database = DatabaseModule(app, dsn=dsn)
  await app.state.database.startup()

  await role_helper.load_roles(app.state.database)

  debug = await app.state.database.get_config_value("DebugLogging")
  configure_root_logging(debug=str(debug).lower() in ["1", "true"])

  mssql_dsn = os.getenv("AZURE_SQL_CONNECTION_STRING")
  app.state.mssql = MSSQLModule(app, dsn=mssql_dsn)
  await app.state.mssql.startup()

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

