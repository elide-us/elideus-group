from fastapi import FastAPI
from contextlib import asynccontextmanager
from server.modules import ModuleRegistry

from server.modules.env_module import EnvironmentModule   # Explicit manual import
from server.modules.discord_module import DiscordModule   # Explicit manual import
from server.modules.database_module import DatabaseModule # Explicit manual import
from server.modules.auth_module import AuthModule         # Explicit manual import

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.env = EnvironmentModule(app)
  app.state.env.startup()
  app.state.discord = DiscordModule(app)
  app.state.discord.startup()
  app.state.database = DatabaseModule(app)
  app.state.database.startup()
  app.state.auth = AuthModule(app)
  app.state.auth.startup()

  mr = ModuleRegistry(app)
  app.state.modules = mr

  # await mr.startup()

  try:
    yield
  finally:
    return

