"""Environment variable loader module."""

import os, dotenv, logging
from fastapi import FastAPI
from . import BaseModule

dotenv.load_dotenv()

class EnvModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self._env: dict[str, str | None] = {}
  
  async def startup(self):
    self._getenv("DISCORD_SECRET", "MISSING_ENV_DISCORD_SECRET")
    self._getenv("DISCORD_AUTH_SECRET", "MISSING_ENV_DISCORD_AUTH_SECRET")
    self._getenv("JWT_SECRET", "MISSING_ENV_JWT_SECRET")
    self._getenv("GOOGLE_AUTH_SECRET", "MISSING_ENV_GOOGLE_AUTH_SECRET")
    self._getenv("DATABASE_PROVIDER", "MISSING_DATABASE_PROVIDER")
    provider = self._env["DATABASE_PROVIDER"]
    if not provider:
      logging.error("No DB provider!")
      raise
    if provider == "mssql":
      self._getenv("AZURE_SQL_CONNECTION_STRING", "MISSING_ENV_AZURE_SQL_CONNECTION_STRING")
    if provider == "postgres":
      self._getenv("POSTGRES_SQL_CONNECTION_STRING", "MISSING_POSTGRES_SQL_CONNECTION_STRING")
    if provider == "mysql":
      self._getenv("MYSQL_SQL_CONNECTION_STRING", "MISSING_MYSQL_SQL_CONNECTION_STRING")
    self._getenv("AZURE_BLOB_CONNECTION_STRING", "MISSING_ENV_AZURE_BLOB_CONNECTION_STRING")

    logging.info("Environment module loaded")
    self.mark_ready()

  async def shutdown(self):
    self._env.clear()

  def _getenv(self, var_name: str, default: str | None = None):
    value = os.getenv(var_name, default)
    if value is None:
      raise RuntimeError(f"ERROR: {var_name} missing.")
    self._env[var_name] = value

  def get(self, var_name: str) -> str | None:
    if var_name not in self._env:
      raise RuntimeError(f"ERROR: {var_name} not initialized in EnvironmentProvider.")
    return self._env[var_name]

  def get_as_int(self, var_name: str) -> int:
    return int(self.get(var_name))
