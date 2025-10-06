from __future__ import annotations

import asyncio
import importlib
import os
import sys
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Dict, Optional, Protocol, runtime_checkable

from fastapi import FastAPI

# Clear any stub module that might shadow the real RPC package during testing.
_rpc_module = sys.modules.get('rpc')
if _rpc_module is not None and not hasattr(_rpc_module, '__path__'):
  sys.modules.pop('rpc', None)

from server.helpers.strings import camel_case
from server.registry import RegistryDispatcher

MODULES_FOLDER = os.path.dirname(__file__)


class ModuleServices(SimpleNamespace):
  """Container for RPC-facing service facades."""

  def __init__(self, **kwargs):
    _ensure_rpc_package()
    super().__init__(**kwargs)

  def require(self, name: str):
    service = getattr(self, name, None)
    if not service:
      raise RuntimeError(f"Service facade '{name}' is not registered")
    return service


@runtime_checkable
class AuthService(Protocol):
  """RPC-safe authentication service facade."""

  def require_role_mask(self, name: str) -> int:
    ...

  async def user_has_role(self, guid: str, required_mask: int) -> bool:
    ...

class BaseModule(ABC):
  def __init__(self, app: FastAPI):
    self.app = app
    self._ready_event = asyncio.Event()

  @abstractmethod
  async def startup(self):
    pass

  @abstractmethod
  async def shutdown(self):
    pass

  def mark_ready(self):
    self._ready_event.set()

  async def on_ready(self):
    await self._ready_event.wait()

  def create_service(self) -> Optional[object]:
    """Return an optional RPC-facing facade for this module."""
    return None

class ModuleManager:
  def __init__(self, app: FastAPI):
    self.app = app
    self.instances: Dict[str, BaseModule] = {}
    self.services = ModuleServices()
    self.registry = RegistryDispatcher()
    self.registry.initialise()
    setattr(app.state, "registry", self.registry)
    setattr(app.state, "services", self.services)

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

      if hasattr(instance, "set_registry"):
        instance.set_registry(self.registry)

      setattr(app.state, module_name, instance)
      self.instances[module_name] = instance

      service = instance.create_service()
      if service is not None:
        setattr(self.services, module_name, service)

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


def _ensure_rpc_package() -> None:
  module = sys.modules.get('rpc')
  if module is None or not hasattr(module, '__path__'):
    importlib.import_module('rpc')


_ensure_rpc_package()
