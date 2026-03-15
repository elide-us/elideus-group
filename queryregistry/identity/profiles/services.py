"""Identity profiles query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  GetPublicProfileParams,
  GuidParams,
  SetDisplayParams,
  SetOptInParams,
  SetProfileImageParams,
  SetRolesParams,
  UpdateIfUneditedParams,
)

__all__ = [
  "read_profile_v1",
  "get_public_profile_v1",
  "get_roles_v1",
  "set_display_v1",
  "set_optin_v1",
  "set_profile_image_v1",
  "set_roles_v1",
  "update_profile_v1",
  "update_profile_if_unedited_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_READ_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.read_profile,
}

_UPDATE_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.update_profile,
}

_UPDATE_IF_UNEDITED_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.update_if_unedited,
}

_GET_ROLES_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.get_roles_v1,
}

_SET_DISPLAY_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.set_display_v1,
}

_SET_OPTIN_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.set_optin_v1,
}

_SET_PROFILE_IMAGE_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.set_profile_image_v1,
}

_SET_ROLES_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.set_roles_v1,
}

_UPDATE_IF_UNEDITED_V1_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.update_if_unedited_v1,
}

_GET_PUBLIC_PROFILE_DISPATCHERS: dict[str, _Dispatcher] = {
  "mssql": mssql.get_public_profile_v1,
}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity profiles registry")
  return dispatcher


def _validate_update_payload(payload: Mapping[str, Any]) -> None:
  has_display_name = "display_name" in payload
  has_display_email = "display_email" in payload
  has_image = "image_b64" in payload
  if not (has_display_name or has_display_email or has_image):
    raise ValueError("Profile update requires at least one field")
  if has_image and not payload.get("provider"):
    raise ValueError("Profile image updates require provider")


async def read_profile_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _READ_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity profiles registry")
  payload = dict(request.payload)
  result = await dispatcher(payload)
  return DBResponse(op=request.op, payload=result.payload)


async def update_profile_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UPDATE_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity profiles registry")
  payload = dict(request.payload)
  _validate_update_payload(payload)
  result = await dispatcher(payload)
  return DBResponse(
    op=request.op,
    payload=result.payload,
    rowcount=result.rowcount,
  )


async def update_profile_if_unedited_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UPDATE_IF_UNEDITED_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity profiles registry")
  payload = dict(request.payload)
  result = await dispatcher(payload)
  return DBResponse(
    op=request.op,
    payload=result.payload,
    rowcount=result.rowcount,
  )


async def get_roles_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GuidParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_ROLES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_display_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetDisplayParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _SET_DISPLAY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_optin_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetOptInParams.model_validate(request.payload)
  payload = params.model_dump()
  payload["display_email"] = 1 if params.display_email else 0
  result = await _select_dispatcher(provider, _SET_OPTIN_DISPATCHERS)(payload)
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_profile_image_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetProfileImageParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _SET_PROFILE_IMAGE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_roles_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = SetRolesParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _SET_ROLES_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_if_unedited_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateIfUneditedParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_IF_UNEDITED_V1_DISPATCHERS)(
    params.model_dump(exclude_none=True)
  )
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_public_profile_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetPublicProfileParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_PUBLIC_PROFILE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
