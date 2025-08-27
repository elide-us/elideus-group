from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from .models import DBResult


class BaseProvider(ABC):
  def __init__(self, **config: Any):
    self.config = config


class LifecycleProvider(BaseProvider):
  @abstractmethod
  async def startup(self) -> None: ...

  @abstractmethod
  async def shutdown(self) -> None: ...


class AuthProviderBase(LifecycleProvider):
  @abstractmethod
  async def verify_id_token(self, id_token: str, access_token: str | None = None) -> Dict[str, Any]: ...

  @abstractmethod
  async def fetch_user_profile(self, access_token: str) -> Dict[str, Any]: ...

  @abstractmethod
  def extract_guid(self, payload: Dict[str, Any]) -> str | None: ...


class DbProviderBase(LifecycleProvider):
  @abstractmethod
  async def run(self, op: str, args: Dict[str, Any]) -> DBResult: ...
