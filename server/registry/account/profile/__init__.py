"""Account profile registry helpers."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest
from .model import (
  GuidParams,
  ProfileRecord,
  SetDisplayParams,
  SetOptInParams,
  SetProfileImageParams,
  SetRolesParams,
  UpdateIfUneditedParams,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "get_profile_request",
  "get_roles_request",
  "set_display_request",
  "set_optin_request",
  "set_profile_image_request",
  "set_roles_request",
  "update_if_unedited_request",
  "register",
  "GuidParams",
  "ProfileRecord",
  "SetDisplayParams",
  "SetOptInParams",
  "SetProfileImageParams",
  "SetRolesParams",
  "UpdateIfUneditedParams",
]


def _request(name: str, params: dict[str, object]) -> DBRequest:
  return DBRequest(op=f"db:account:profile:{name}:1", payload=params)


def get_profile_request(params: GuidParams) -> DBRequest:
  return _request("get_profile", params.model_dump())


def get_roles_request(params: GuidParams) -> DBRequest:
  return _request("get_roles", params.model_dump())


def set_display_request(params: SetDisplayParams) -> DBRequest:
  return _request("set_display", params.model_dump())


def set_optin_request(params: SetOptInParams) -> DBRequest:
  payload = params.model_dump()
  payload["display_email"] = 1 if params.display_email else 0
  return _request("set_optin", payload)


def set_profile_image_request(params: SetProfileImageParams) -> DBRequest:
  return _request("set_profile_image", params.model_dump())


def set_roles_request(params: SetRolesParams) -> DBRequest:
  return _request("set_roles", params.model_dump())


def update_if_unedited_request(params: UpdateIfUneditedParams) -> DBRequest:
  return _request("update_if_unedited", params.model_dump(exclude_none=True))


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="get_profile", version=1)
  register_op(name="get_roles", version=1)
  register_op(name="set_display", version=1)
  register_op(name="set_optin", version=1)
  register_op(name="set_profile_image", version=1)
  register_op(name="set_roles", version=1)
  register_op(name="update_if_unedited", version=1)
