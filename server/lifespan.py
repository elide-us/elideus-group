from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from server.modules.env_module import EnvironmentModule
from server.modules.discord_module import DiscordModule
from server.modules.database_module import DatabaseModule
from server.modules.auth_module import AuthModule
from server.helpers.logging import configure_root_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
  dsn = os.getenv("POSTGRES_CONNECTION_STRING")
  app.state.database = DatabaseModule(app, dsn=dsn)
  await app.state.database.startup()

  debug = await app.state.database.get_config_value("DebugLogging")
  configure_root_logging(debug=str(debug).lower() in ["1", "true"])

  app.state.env = EnvironmentModule(app)
  app.state.discord = DiscordModule(app)
  await app.state.discord.startup()
  app.state.auth = AuthModule(app)
  await app.state.auth.startup()

  try:
    yield
  finally:
    return

