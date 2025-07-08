import os, json
from pathlib import Path
import dotenv
from fastapi import FastAPI
from server.providers import Provider

dotenv.load_dotenv()

class EnvironmentProvider(Provider):
  def __init__(self, app: FastAPI):
    super().__init__(app)

    # Use internal dict to store all loaded values
    self._env: dict[str, str] = {}
    self._version: dict[str, str] = {}

  async def startup(self):
    self._load_version_file()
    self._load_required("HOSTNAME", "MISSING_ENV_HOSTNAME")
    self._load_required("REPO", "MISSING_ENV_REPO")
    self._load_required("DISCORD_SECRET", "MISSING_ENV_DISCORD_SECRET")
    self._load_required("DISCORD_SYSCHAN", 0)

  async def shutdown(self):
    # Nothing to clean up, but defined for interface compliance
    pass

  def _load_version_file(self):
    path = Path('version.json')
    if path.exists():
      with path.open() as f:
        self._version = json.load(f)
    else:
      self._version = {"tag": "v0.0.0", "commit": "unknown"}
    self._env["VERSION"] = f"{self._version.get('tag')}.{self._version.get('commit')}"

  def get_version_info(self) -> dict[str, str]:
    return self._version

  def _load_required(self, var_name: str, default: str | None = None):
    value = os.getenv(var_name, default)
    if value is None:
      raise RuntimeError(f"ERROR: {var_name} missing.")
    self._env[var_name] = value

  def get(self, var_name: str) -> str:
    if var_name not in self._env:
      raise RuntimeError(f"ERROR: {var_name} not initialized in EnvironmentProvider.")
    return self._env[var_name]

  def get_int(self, var_name: str) -> int:
    return int(self.get(var_name))
