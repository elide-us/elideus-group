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

# class ProviderRegistry:
#   def __init__(self, app: FastAPI):
#     self.app = app
#     self.providers: dict[str, Provider] = {}
#     self._discover_and_register_providers()

#   def _discover_and_register_providers(self):
#     for _, module_name, _ in pkgutil.iter_modules(__path__):
#       if module_name.endswith("_provider"):
#         module = importlib.import_module(f"{__name__}.{module_name}")
#         for name, obj in inspect.getmembers(module, inspect.isclass):
#           if issubclass(obj, Provider) and obj is not Provider:
#             key = module_name.replace("_provider", "")
#             instance = obj(self.app)
#             self.providers[key] = instance
#             setattr(self.app.state, f"{key}_provider", instance)

#   async def startup(self):
#     for provider in self.providers.values():
#       await provider.startup()

#   async def shutdown(self):
#     for provider in self.providers.values():
#       await provider.shutdown()

from server.providers.env_provider import EnvironmentProvider  # Explicit manual import

class ProviderRegistry:
  def __init__(self, app: FastAPI):
    self.app = app
    self.providers: dict[str, Provider] = {}

    # Step 1: Manually register 'env' first
    env_provider = EnvironmentProvider(app)
    self.providers["env"] = env_provider
    setattr(self.app.state, "env_provider", env_provider)

    # Step 2: Dynamically register all other providers
    self._discover_and_register_providers(exclude={"env_provider"})

  def _discover_and_register_providers(self, exclude: set[str] = set()):
    for _, module_name, _ in pkgutil.iter_modules(__path__):
      if module_name.endswith("_provider") and module_name not in exclude:
        module = importlib.import_module(f"{__name__}.{module_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
          if issubclass(obj, Provider) and obj is not Provider:
            key = module_name.replace("_provider", "")
            if key in self.providers:
              continue  # already registered (e.g. env)
            instance = obj(self.app)
            self.providers[key] = instance
            setattr(self.app.state, f"{key}_provider", instance)

  async def startup(self):
    for key, provider in self.providers.items():
      await provider.startup()

  async def shutdown(self):
    for key, provider in reversed(self.providers.items()):
      await provider.shutdown()
