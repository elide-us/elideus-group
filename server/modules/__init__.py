import logging
from abc import ABC, abstractmethod
from fastapi import FastAPI

class BaseModule(ABC):
  def __init__(self, app: FastAPI):
    self.app = app

  @abstractmethod
  async def startup(self):
    pass

  @abstractmethod
  async def shutdown(self):
    pass

from server.modules.env_module import EnvironmentModule   # Explicit manual import
from server.modules.discord_module import DiscordModule   # Explicit manual import
from server.modules.database_module import DatabaseModule # Explicit manual import
from server.modules.auth_module import AuthModule         # Explicit manual import

class ModuleRegistry:
  def __init__(self, app: FastAPI):
    self.app = app
    self.modules: dict[str, BaseModule] = {}
    setattr(self.app.state, "modules", self)

    # Step 1: Manually register 'env' first
    env_module = EnvironmentModule(app)
    self.modules["env"] = env_module
    setattr(self.app.state, "env_module", env_module)

    # Step 2: Manually register 'discord' second
    discord_module = DiscordModule(app)
    self.modules["discord"] = discord_module
    setattr(self.app.state, "discord_module", discord_module)

    # Step 3: Manually register 'database' third
    database_module = DatabaseModule(app)
    self.modules["database"] = database_module
    setattr(self.app.state, "database_module", database_module)

    # Step 4: Manually register 'auth' fourth
    auth_module = AuthModule(app)
    self.modules["auth"] = auth_module
    setattr(self.app.state, "auth_module", auth_module)

  def get_module(self, key: str) -> BaseModule:
    if key not in self.modules:
      raise KeyError(f"Module '{key}' not registered")
    return self.modules[key]


  async def startup(self):
    for key, module in self.modules.items():
      await module.startup()
      logging.info(f"Module '{key}' started")

  async def shutdown(self):
    for key, module in reversed(list(self.modules.items())):
      await module.shutdown()
      logging.info(f"Module '{key}' shutdown")
