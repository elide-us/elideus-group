import os, dotenv

dotenv.load_dotenv()

def get_environment_variable(var_name: str, default: str | None = None) -> str:
  value = os.getenv(var_name, default)
  if value is None:
    raise RuntimeError(f"ERROR: {var_name} missing.")
  return value

VERSION = get_environment_variable("VERSION", "MISSING_ENV_VERSION")
HOSTNAME = get_environment_variable("HOSTNAME", "MISSING_ENV_HOSTNAME")
REPO = get_environment_variable("REPO", "MISSING_ENV_REPO")

def get_discord_secret():
  return get_environment_variable("DISCORD_SECRET", "MISSING_ENV_DISCORD_SECRET")

def get_discord_syschan():
  return 1391617075843174531