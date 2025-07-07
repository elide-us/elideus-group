import pkgutil, importlib, inspect
from abc import ABC, abstractmethod
from fastapi import FastAPI

class Provider(ABC):
  def __init__(self, app: FastAPI):
    self.app = app

  @abstractmethod
  async def startup(self):
    pass

  @abstractmethod
  async def shutdown(self):
    pass

class ProviderRegistry:
  def __init__(self, app: FastAPI):
    self.app = app
    self.providers: dict[str, Provider] = {}
    self._discover_and_register_providers()

  def _discover_and_register_providers(self):
    for _, module_name, _ in pkgutil.iter_modules(__path__):
      if module_name.endswith("_provider"):
        module = importlib.import_module(f"{__name__}.{module_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
          if issubclass(obj, Provider) and obj is not Provider:
            key = module_name.replace("_provider", "")
            instance = obj(self.app)
            self.providers[key] = instance
            setattr(self.app.state, f"{key}_provider", instance)

  async def startup(self):
    for provider in self.providers.values():
      await provider.startup()

  async def shutdown(self):
    for provider in self.providers.values():
      await provider.shutdown()

