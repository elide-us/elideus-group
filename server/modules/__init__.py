from abc import ABC, abstractmethod
from fastapi import FastAPI

class BaseModule(ABC):
  def __init__(self, app: FastAPI):
    self.app = app

class ModuleRegistry:
  def __init__(self, app: FastAPI):
    self.app = app
    self.modules: dict[str, BaseModule] = {}
    
  def get_module(self, key: str) -> BaseModule:
    if key not in self.modules:
      raise KeyError(f"Module '{key}' not registered")
    return self.modules[key]

  #def register_module(self, key: str) -> BaseModule:

  #def unregister_module(self, key: str): # consider Pydantic model for return contract