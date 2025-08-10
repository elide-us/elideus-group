from abc import ABC, abstractmethod
from fastapi import FastAPI
from typing import Type, Dict, List
from scripts.genlib import camel_case
import asyncio, os, importlib

MODULES_FOLDER = os.path.dirname(__file__)

class BaseModule(ABC):
  def __init__(self, app: FastAPI):
    self.app = app
    self._ready_event = asyncio.Event()

  @abstractmethod
  async def startup():
    pass

  @abstractmethod
  async def shutdown():
    pass

  def mark_ready(self):
    self._ready_event.set()

  async def on_ready(self):
    await self._ready_event.wait()

class ModuleManager:
  def __init__(self, app: FastAPI):
    self.app = app
    self.instances: Dict[str, BaseModule] = {}

    for fname in os.listdir(MODULES_FOLDER):
      if not fname.endswith("_module.py") or fname == "__init__.py":
        continue

      file_name = fname[:-3]  # strip '.py'
      module_name = file_name[:-7]
      class_name = camel_case(file_name.removesuffix("_module")) + "Module"
      module_path = f"{__name__}.{file_name}"

      mod = importlib.import_module(module_path)
      if not hasattr(mod, class_name):
        raise ImportError(f"Module '{file_name}' missing expected class '{class_name}'")
      cls = getattr(mod, class_name)
      instance = cls(app)

      setattr(app.state, module_name, instance)
      self.instances[module_name] = instance

  async def startup_all(self):
    await asyncio.gather(*(mod.startup() for mod in self.instances.values()))

  async def shutdown_all(self):
    await asyncio.gather(*(mod.shutdown() for mod in self.instances.values()))
    for name in self.instances:
      setattr(self.app.state, name, None)
  
  async def restart(self, name: str):
    instance = self.instances.get(name)
    if not instance:
      raise ValueError(f"Module '{name}' not found.")
    await instance.shutdown()
    new_instance = type(instance)(self.app)
    setattr(self.app.state, name, new_instance)
    await new_instance.startup()
    self.instances[name] = new_instance
