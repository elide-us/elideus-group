from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


def _stou(value: str) -> UUID:
  return UUID(value)


def _utos(value: UUID) -> str:
  return str(value)


class DatabaseProvider(ABC):
  @abstractmethod
  async def select_user(self, provider: str, provider_user_id: str):
    pass

  @abstractmethod
  async def insert_user(self, provider: str, provider_user_id: str, email: str, username: str):
    pass

  @abstractmethod
  async def get_user_profile(self, guid: str):
    pass

  @abstractmethod
  async def get_user_roles(self, guid: str) -> int:
    pass

  @abstractmethod
  async def list_roles(self) -> list[dict]:
    pass

  @abstractmethod
  async def set_role(self, name: str, mask: int, display: str):
    pass

  @abstractmethod
  async def delete_role(self, name: str):
    pass

  @abstractmethod
  async def get_user_enablements(self, guid: str) -> int:
    pass

  @abstractmethod
  async def select_routes(self, role_mask: int = 0):
    pass

  @abstractmethod
  async def list_routes(self) -> list[dict]:
    pass

  @abstractmethod
  async def set_route(self, path: str, name: str, icon: str, required_roles: int, sequence: int):
    pass

  @abstractmethod
  async def delete_route(self, path: str):
    pass

  @abstractmethod
  async def select_links(self, role_mask: int = 0):
    pass

  @abstractmethod
  async def get_config_value(self, key: str) -> str | None:
    pass

  @abstractmethod
  async def set_config_value(self, key: str, value: str):
    pass

  @abstractmethod
  async def list_config(self) -> list[dict]:
    pass

  @abstractmethod
  async def delete_config_value(self, key: str):
    pass

  @abstractmethod
  async def update_display_name(self, guid: str, display_name: str):
    pass

  @abstractmethod
  async def select_users(self):
    pass

  @abstractmethod
  async def select_users_with_role(self, mask: int):
    pass

  @abstractmethod
  async def select_users_without_role(self, mask: int):
    pass

  @abstractmethod
  async def set_user_roles(self, guid: str, roles: int):
    pass

  @abstractmethod
  async def set_user_credits(self, guid: str, credits: int):
    pass

  @abstractmethod
  async def set_user_rotation_token(self, guid: str, token: str, expires: datetime):
    pass

  @abstractmethod
  async def create_user_session(self, user_guid: str, bearer: str, rotation: str, expires: datetime) -> str:
    pass

  @abstractmethod
  async def get_session_by_rotation(self, rotation_token: str):
    pass

  @abstractmethod
  async def update_session_tokens(self, session_id: str, bearer: str, rotation: str, expires: datetime):
    pass

  @abstractmethod
  async def delete_session(self, session_id: str):
    pass

  @abstractmethod
  async def get_user_profile_image(self, guid: str) -> str | None:
    pass

  @abstractmethod
  async def set_user_profile_image(self, guid: str, image_b64: str, provider: str | None = None):
    pass
