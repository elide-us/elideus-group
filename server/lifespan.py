from fastapi import FastAPI
from contextlib import asynccontextmanager

from server.modules.env_module import EnvironmentModule   # Explicit manual import
from server.modules.discord_module import DiscordModule   # Explicit manual import
from server.modules.database_module import DatabaseModule # Explicit manual import
from server.modules.auth_module import AuthModule         # Explicit manual import

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.env = EnvironmentModule(app)
  app.state.discord = DiscordModule(app)

  app.state.database = DatabaseModule(app)
  await app.state.database.startup()

  app.state.auth = AuthModule(app)
  await app.state.auth.startup()

  try:
    yield
  finally:
    return

