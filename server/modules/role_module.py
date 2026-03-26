"""Role management module for system role definitions and user role lookups."""

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI

from queryregistry.identity.roles import get_roles_request
from queryregistry.identity.roles.models import UserGuidParams
from queryregistry.system.roles import (
  delete_system_role_request,
  list_system_roles_request,
  update_system_role_request,
)
from queryregistry.system.roles.models import DeleteRoleParams, UpsertRoleParams

from . import BaseModule
from .db_module import DbModule


class RoleModule(BaseModule):
  """Owns system role definitions, user role lookups, and bitmask utilities."""

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.roles: dict[str, int] = {}
    self.role_names: list[str] = []
    self.role_registered: int = 0
    self.domain_role_map: dict[str, int] = {}
    self._user_roles: dict[str, tuple[list[str], int]] = {}

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    await self.load_roles()
    await self.load_domain_role_map()
    self.app.state.role = self
    logging.debug("[RoleModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  @staticmethod
  def _normalize_payload(payload: Any | None) -> list[dict[str, Any]]:
    if payload is None:
      return []
    if isinstance(payload, list):
      return [dict(item) for item in payload]
    if isinstance(payload, Mapping):
      return [dict(payload)]
    return [dict(payload)]

  async def load_roles(self):
    assert self.db
    logging.debug("[RoleModule] Loading roles from database")
    try:
      result = await self.db.run(list_system_roles_request())
    except Exception as e:
      logging.error("[RoleModule] Failed to load roles: %s", e)
      return
    rows = self._normalize_payload(result.payload)
    if not rows:
      logging.debug("[RoleModule] No roles returned")
      return
    self.roles.clear()
    for role in rows:
      name = role.get("name")
      if not name:
        continue
      self.roles[name] = int(role.get("mask", 0) or 0)
    self.role_registered = self.roles.get("ROLE_REGISTERED", 0)
    self.role_names = [name for name in self.roles.keys() if name != "ROLE_REGISTERED"]
    self._user_roles.clear()
    logging.debug("[RoleModule] Loaded roles: %s", self.roles)

  async def load_domain_role_map(self):
    assert self.db
    logging.debug("[RoleModule] Loading RPC domain role map")
    result = await self.db.run(list_system_roles_request())
    rows = self._normalize_payload(result.payload)
    self.domain_role_map = {}
    for row in rows:
      domain = row.get("element_rpc_domain")
      if not domain:
        continue
      self.domain_role_map[str(domain)] = int(row.get("mask", 0) or 0)
    logging.debug("[RoleModule] Loaded domain role map: %s", self.domain_role_map)

  async def refresh_role_cache(self):
    await self.load_roles()
    await self.load_domain_role_map()

  async def upsert_role(self, name: str, mask: int, display: str | None):
    assert self.db
    payload = UpsertRoleParams(name=name, mask=mask, display=display)
    await self.db.run(update_system_role_request(payload))
    await self.refresh_role_cache()

  async def delete_role(self, name: str):
    assert self.db
    payload = DeleteRoleParams(name=name)
    await self.db.run(delete_system_role_request(payload))
    await self.refresh_role_cache()

  def mask_to_names(self, mask: int) -> list[str]:
    return [name for name, bit in self.roles.items() if mask & bit]

  def names_to_mask(self, names: list[str]) -> int:
    mask = 0
    for name in names:
      mask |= self.roles.get(name, 0)
    return mask

  def get_role_names(self, exclude_registered: bool = False) -> list[str]:
    if exclude_registered:
      return list(self.role_names)
    return list(self.roles.keys())

  async def get_user_roles(self, guid: str, refresh: bool = False) -> tuple[list[str], int]:
    if not refresh and guid in self._user_roles:
      return self._user_roles[guid]
    assert self.db
    response = await self.db.run(get_roles_request(UserGuidParams(guid=guid)))
    rows = self._normalize_payload(response.payload)
    row = rows[0] if rows else {}
    mask = int(row.get("roles") or row.get("user_roles") or row.get("element_roles") or 0)
    names = self.mask_to_names(mask)
    self._user_roles[guid] = (names, mask)
    logging.debug("[RoleModule] Roles for %s: %s (mask=%#018x)", guid, names, mask)
    return names, mask

  async def user_has_role(self, guid: str, required_mask: int) -> bool:
    if not required_mask:
      return True
    if not guid:
      return False
    _, mask = await self.get_user_roles(guid)
    return bool(mask & required_mask)

  async def refresh_user_roles(self, guid: str):
    await self.get_user_roles(guid, refresh=True)
