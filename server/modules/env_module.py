import os, dotenv, logging
from fastapi import FastAPI
from server.modules import BaseModule

dotenv.load_dotenv()

class EnvironmentModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)

    # Use internal dict to store all loaded values
    self._env: dict[str, str | None] = {}
    self._version: dict[str, str] = {}

  async def startup(self):
    self._load_required("VERSION", "MISSING_ENV_VERSION")
    self._load_required("HOSTNAME", "MISSING_ENV_HOSTNAME")
    self._load_required("REPO", "MISSING_ENV_REPO")
    self._load_required("DISCORD_SECRET", "MISSING_ENV_DISCORD_SECRET")
    self._load_required("DISCORD_SYSCHAN", 0)
    self._load_optional("JWT_SECRET")
    self._load_optional("MS_API_ID")
    self._load_optional("POSTGRES_CONNECTION_STRING")
    logging.info("Environment module loaded")

  async def shutdown(self):
    # Nothing to clean up, but defined for interface compliance
    pass

  def _load_required(self, var_name: str, default: str | None = None):
    value = os.getenv(var_name, default)
    if value is None:
      raise RuntimeError(f"ERROR: {var_name} missing.")
    self._env[var_name] = value

  def _load_optional(self, var_name: str, default: str | None = None):
    value = os.getenv(var_name, default)
    self._env[var_name] = value

  def get(self, var_name: str) -> str | None:
    if var_name not in self._env:
      raise RuntimeError(f"ERROR: {var_name} not initialized in EnvironmentProvider.")
    return self._env[var_name]

  def get_int(self, var_name: str) -> int:
    return int(self.get(var_name))
