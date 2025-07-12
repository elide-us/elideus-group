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

# from server.modules.env_module import EnvironmentModule   # Explicit manual import
# from server.modules.discord_module import DiscordModule   # Explicit manual import
# from server.modules.database_module import DatabaseModule # Explicit manual import
# from server.modules.auth_module import AuthModule         # Explicit manual import

class ModuleRegistry:
  def __init__(self, app: FastAPI):
    self.app = app
    self.modules: dict[str, BaseModule] = {}
    setattr(self.app.state, "modules", self)

    # Step 1: Manually register 'env' first
    #env_module = EnvironmentModule(app)
    self.modules["env"] = app.state.env
    setattr(self.app.state, "env_module", app.state.env)

    # Step 2: Manually register 'discord' second
    #discord_module = DiscordModule(app)
    self.modules["discord"] = app.state.discord
    setattr(self.app.state, "discord_module", app.state.discord)

    # Step 3: Manually register 'database' third
    #database_module = DatabaseModule(app)
    self.modules["database"] = app.state.database
    setattr(self.app.state, "database_module", app.state.database)

    # Step 4: Manually register 'auth' fourth
    #auth_module = AuthModule(app)
    self.modules["auth"] = app.state.auth
    setattr(self.app.state, "auth_module", app.state.auth)

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
