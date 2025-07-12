import os, dotenv, logging
from fastapi import FastAPI

dotenv.load_dotenv()

class EnvironmentModule():
  def __init__(self, app: FastAPI):
    self.app = app

    self._env: dict[str, str | None] = {}
    self._getenv("VERSION", "MISSING_ENV_VERSION")
    self._getenv("HOSTNAME", "MISSING_ENV_HOSTNAME")
    self._getenv("REPO", "MISSING_ENV_REPO")
    self._getenv("DISCORD_SECRET", "MISSING_ENV_DISCORD_SECRET")
    self._getenv("DISCORD_SYSCHAN", 0)
    self._getenv("JWT_SECRET", "MISSING_ENV_JWT_SECRET")
    self._getenv("MS_API_ID", "MISSING_ENV_MS_API_ID")
    self._getenv("POSTGRES_CONNECTION_STRING", "MISSING_ENV_POSTGRES_CONNECTION_STRING")
    
    logging.info("Environment module loaded")

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
