"""User profile registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from . import mssql as profile_mssql

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "mssql",
  "get_profile_request",
  "set_display_request",
  "set_optin_request",
  "set_profile_image_request",
  "set_roles_request",
  "update_if_unedited_request",
  "register",
]

mssql = profile_mssql


def _request(name: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:users:profile:{name}:1", params=params)


def get_profile_request(*, guid: str) -> DBRequest:
  return _request("get_profile", {"guid": guid})


def set_display_request(*, guid: str, display_name: str) -> DBRequest:
  return _request("set_display", {"guid": guid, "display_name": display_name})


def set_optin_request(*, guid: str, display_email: bool) -> DBRequest:
  return _request("set_optin", {"guid": guid, "display_email": display_email})


def set_profile_image_request(
  *,
  guid: str,
  provider: str,
  image_b64: str | None,
) -> DBRequest:
  params: dict[str, Any] = {
    "guid": guid,
    "provider": provider,
    "image_b64": image_b64,
  }
  return _request("set_profile_image", params)


def set_roles_request(*, guid: str, roles: int) -> DBRequest:
  return _request("set_roles", {"guid": guid, "roles": roles})


def update_if_unedited_request(
  *,
  guid: str,
  display_name: str | None = None,
  email: str | None = None,
) -> DBRequest:
  params: dict[str, Any] = {"guid": guid}
  if display_name is not None:
    params["display_name"] = display_name
  if email is not None:
    params["email"] = email
  return _request("update_if_unedited", params)


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_profile", version=1)
  router.add_function("set_display", version=1)
  router.add_function("set_optin", version=1)
  router.add_function("set_profile_image", version=1)
  router.add_function("set_roles", version=1)
  router.add_function("update_if_unedited", version=1)
