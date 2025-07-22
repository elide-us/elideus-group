from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from server.modules.env_module import EnvironmentModule
from server.modules.discord_module import DiscordModule
from server.modules.database_module import DatabaseModule
from server.modules.auth_module import AuthModule
from server.modules.permcap_module import PermCapModule
from server.modules.storage_module import StorageModule
from server.helpers.logging import configure_root_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
  dsn = os.getenv("POSTGRES_CONNECTION_STRING")
  app.state.database = DatabaseModule(app, dsn=dsn)
  await app.state.database.startup()
  from server.helpers import roles as role_helper
  await role_helper.load_roles(app.state.database)

  debug = await app.state.database.get_config_value("DebugLogging")
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

