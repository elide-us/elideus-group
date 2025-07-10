import pkgutil, importlib, inspect, logging
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

from server.modules.env_module import EnvironmentModule  # Explicit manual import

class ModuleRegistry:
  def __init__(self, app: FastAPI):
    self.app = app
    self.modules: dict[str, BaseModule] = {}
    setattr(self.app.state, "modules", self)

    # Step 1: Manually register 'env' first
    env_module = EnvironmentModule(app)
    self.modules["env"] = env_module
    setattr(self.app.state, "env_module", env_module)

    # Step 2: Dynamically register all other providers
    self._discover_and_register_modules(exclude={"env_module"})

  def get_module(self, key: str) -> BaseModule:
    if key not in self.modules:
      raise KeyError(f"Module '{key}' not registered")
    return self.modules[key]

  def _discover_and_register_modules(self, exclude: set[str] = set()):
    for _, module_name, _ in pkgutil.iter_modules(__path__):
      if module_name.endswith("_module") and module_name not in exclude:
        module = importlib.import_module(f"{__name__}.{module_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
          if issubclass(obj, BaseModule) and obj is not BaseModule:
            key = module_name.replace("_module", "")
            if key in self.modules:
              continue  # already registered (e.g. env)
            instance = obj(self.app)
            self.modules[key] = instance
            setattr(self.app.state, f"{key}_module", instance)

  async def startup(self):
    for key, module in self.modules.items():
      await module.startup()
      logging.info(f"Module '{key}' started")

  async def shutdown(self):
    for key, module in reversed(list(self.modules.items())):
      await module.shutdown()
      logging.info(f"Module '{key}' shutdown")
