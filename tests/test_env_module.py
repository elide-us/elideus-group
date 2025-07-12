import pytest
from server.modules.env_module import EnvironmentModule


def test_env_loads(app_with_env):
  env = app_with_env.state.env
  assert env.get("VERSION") == "1"
  assert env.get_as_int("DISCORD_SYSCHAN") == 1

def test_env_missing_key(app_with_env):
  env = app_with_env.state.env
  with pytest.raises(RuntimeError):
    env.get("NOPE")
