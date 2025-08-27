from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from server.helpers.logging import configure_root_logging

from server.modules.env_module import EnvironmentModule
from server.modules.storage_module import StorageModule
from server.modules.discord_module import DiscordModule
from server.modules.auth_module import AuthModule
from server.modules.permcap_module import PermCapModule
from server.modules.mssql_provider import MSSQLProvider
from server.modules import LifecycleProvider

from server.helpers import roles as role_helper

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.env = EnvironmentModule(app)

  providers: list[LifecycleProvider] = []

  mssql_dsn = os.getenv("AZURE_SQL_CONNECTION_STRING")
  app.state.mssql = MSSQLProvider(app, dsn=mssql_dsn)
  providers.append(app.state.mssql)

  app.state.storage = StorageModule(app)
  providers.append(app.state.storage)

  app.state.discord = DiscordModule(app)
  providers.append(app.state.discord)

  app.state.auth = AuthModule(app)
  providers.append(app.state.auth)

  app.state.permcap = PermCapModule(app)
  providers.append(app.state.permcap)

  for provider in providers:
    await provider.startup()
    if provider is app.state.mssql:
      await role_helper.load_roles(app.state.mssql)
      debug = await app.state.mssql.get_config_value("DebugLogging")
      configure_root_logging(debug=str(debug).lower() in ["1", "true"])

  try:
    yield
  finally:
    for provider in reversed(providers):
      await provider.shutdown()

