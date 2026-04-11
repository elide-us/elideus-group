from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI

from queryregistry.providers.mssql import run_json_many, run_json_one

from . import BaseModule
from .auth_module import AuthModule
from .db_module import DbModule
from .role_module import RoleModule

_GET_RPC_GATEWAY_SQL = """
SELECT key_guid, pub_name, ref_transport_guid, pub_description, ref_module_guid, pub_is_active
FROM system_objects_io_gateways
WHERE pub_name = ?
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
"""

_LIST_IDENTITY_STRATEGIES_SQL = """
SELECT ip.key_guid, ip.ref_strategy_guid, ip.pub_priority, ip.pub_description,
       v.pub_name AS strategy_name
FROM system_objects_gateway_identity_providers ip
JOIN service_enum_values v ON v.key_guid = ip.ref_strategy_guid
WHERE ip.ref_gateway_guid = ?
  AND ip.pub_is_active = 1
ORDER BY ip.pub_priority
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_METHOD_BINDINGS_SQL = """
SELECT mb.key_guid, mb.pub_operation_name, mb.pub_required_scope,
       mb.ref_required_role_guid, mb.ref_required_entitlement_guid,
       mb.pub_is_read_only, mb.pub_is_active,
       mm.pub_name AS method_name, mod.pub_state_attr AS module_attr
FROM system_objects_gateway_method_bindings mb
JOIN system_objects_module_methods mm ON mm.key_guid = mb.ref_method_guid
JOIN system_objects_modules mod ON mod.key_guid = mm.ref_module_guid
WHERE mb.ref_gateway_guid = ?
  AND mb.pub_is_active = 1
ORDER BY mb.pub_operation_name
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""

_LIST_USER_ENTITLEMENTS_SQL = """
SELECT e.key_guid, e.pub_name
FROM system_user_entitlements ue
JOIN system_auth_entitlements e ON e.key_guid = ue.ref_entitlement_guid
WHERE ue.ref_user_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, INCLUDE_NULL_VALUES;
"""


class RpcIoServiceModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.auth: AuthModule | None = None
    self.role: RoleModule | None = None
    self.gateway_guid: str = ""
    self.strategies: list[dict[str, Any]] = []
    self.bindings: dict[str, dict[str, Any]] = {}

  async def startup(self):
    try:
      self.db = self.app.state.db
      await self.db.on_ready()
      self.auth = self.app.state.auth
      await self.auth.on_ready()
      self.role = self.app.state.role
      await self.role.on_ready()

      gateway_result = await run_json_one(_GET_RPC_GATEWAY_SQL, ("rpc",))
      gateway_row = self._coerce_row(gateway_result.rows if gateway_result else None)
      if not gateway_row:
        raise RuntimeError("RPC gateway registration was not found in system_objects_io_gateways")

      self.gateway_guid = str(gateway_row.get("key_guid") or "")
      if not self.gateway_guid:
        raise RuntimeError("RPC gateway registration is missing key_guid")

      strategies_result = await run_json_many(_LIST_IDENTITY_STRATEGIES_SQL, (self.gateway_guid,))
      strategy_rows = strategies_result.rows if strategies_result and strategies_result.rows else []
      self.strategies = [self._coerce_dict(row) for row in strategy_rows]

      bindings_result = await run_json_many(_LIST_METHOD_BINDINGS_SQL, (self.gateway_guid,))
      binding_rows = bindings_result.rows if bindings_result and bindings_result.rows else []
      self.bindings = {
        str(row.get("pub_operation_name")): self._coerce_dict(row)
        for row in binding_rows
        if row.get("pub_operation_name")
      }

      logging.info(
        "[RpcIoServiceModule] Loaded gateway=%s strategies=%s method_bindings=%s",
        self.gateway_guid,
        len(self.strategies),
        len(self.bindings),
      )
      self.mark_ready()
    except Exception:
      logging.exception("[RpcIoServiceModule] startup failed")
      raise

  async def shutdown(self):
    self.gateway_guid = ""
    self.strategies = []
    self.bindings = {}
    self.db = None
    self.auth = None
    self.role = None

  async def resolve_identity(self, bearer_token: str | None, discord_id: str | None = None) -> dict[str, Any] | None:
    assert self.auth
    assert self.role

    for strategy in self.strategies:
      strategy_name = str(strategy.get("strategy_name") or "")

      if strategy_name == "bearer_jwt" and bearer_token:
        try:
          claims = await self.auth.decode_session_token(bearer_token)
          user_guid = str(claims.get("sub") or "")
          if not user_guid:
            continue
          roles, role_mask = await self.role.get_user_roles(user_guid)
          entitlements = await self._get_user_entitlements(user_guid)
          return {
            "user_guid": user_guid,
            "roles": roles,
            "role_mask": role_mask,
            "entitlements": entitlements,
            "session_type": str(claims.get("session_type") or "browser"),
            "scopes": claims.get("scopes") or [],
            "source": "bearer_jwt",
          }
        except Exception:
          logging.debug("[RpcIoServiceModule] bearer_jwt strategy failed", exc_info=True)

      if strategy_name == "discord_user_id" and discord_id:
        try:
          user_guid, roles, role_mask = await self.auth.get_discord_user_security(discord_id)
          if not user_guid:
            continue
          entitlements = await self._get_user_entitlements(user_guid)
          return {
            "user_guid": user_guid,
            "roles": roles,
            "role_mask": role_mask,
            "entitlements": entitlements,
            "session_type": "bot",
            "scopes": [],
            "source": "discord_user_id",
          }
        except Exception:
          logging.debug("[RpcIoServiceModule] discord_user_id strategy failed", exc_info=True)

    return None

  async def check_authorization(self, identity: dict[str, Any], operation_name: str) -> bool:
    binding = self.bindings.get(operation_name)
    if not binding:
      return False

    required_role = binding.get("ref_required_role_guid")
    if required_role:
      roles = {str(role).upper() for role in (identity.get("roles") or [])}
      if str(required_role).upper() not in roles:
        return False

    required_entitlement = binding.get("ref_required_entitlement_guid")
    if required_entitlement:
      entitlements = {str(entitlement).upper() for entitlement in (identity.get("entitlements") or [])}
      if str(required_entitlement).upper() not in entitlements:
        return False

    return True

  async def get_binding(self, operation_name: str) -> dict[str, Any] | None:
    return self.bindings.get(operation_name)

  async def _get_user_entitlements(self, user_guid: str) -> list[str]:
    result = await run_json_many(_LIST_USER_ENTITLEMENTS_SQL, (user_guid,))
    rows = result.rows if result and result.rows else []
    entitlements: list[str] = []
    for row in rows:
      row_dict = self._coerce_dict(row)
      entitlement_guid = row_dict.get("key_guid")
      if entitlement_guid:
        entitlements.append(str(entitlement_guid))
    return entitlements

  @staticmethod
  def _coerce_row(rows: Any) -> dict[str, Any] | None:
    if not rows:
      return None
    if isinstance(rows, Mapping):
      return dict(rows)
    if isinstance(rows, list) and rows:
      first = rows[0]
      if isinstance(first, Mapping):
        return dict(first)
    return None

  @staticmethod
  def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
      return dict(value)
    return {}
