import os, dotenv

dotenv.load_dotenv()

def _get_str_env_var(var_name: str, default: str | None = None) -> str:
  value = os.getenv(var_name, default)
  if value is None:
    raise RuntimeError(f"ERROR: {var_name} missing.")
  return value

VERSION = _get_str_env_var("VERSION", "unset")
HOSTNAME = _get_str_env_var("HOSTNAME", "unset")
REPO = _get_str_env_var("REPO", "unset")


