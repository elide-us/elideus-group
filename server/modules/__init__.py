from abc import ABC, abstractmethod
from fastapi import FastAPI


class BaseProvider(ABC):
  def __init__(self, app: FastAPI):
    self.app = app


class LifecycleProvider(BaseProvider):
  @abstractmethod
  async def startup(self):
    pass

  @abstractmethod
  async def shutdown(self):
    pass
