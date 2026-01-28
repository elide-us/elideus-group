"""Identity profiles query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  ProfileReadCallable,
  ProfileReadRequestPayload,
  ProfileUpdateCallable,
  ProfileUpdateIfUneditedCallable,
  ProfileUpdateRequestPayload,
  UpdateIfUneditedRequestPayload,
)

__all__ = [
  "read_profile_v1",
  "update_profile_v1",
  "update_profile_if_unedited_v1",
]

_READ_DISPATCHERS: dict[str, ProfileReadCallable] = {
  "mssql": mssql.read_profile,
}

_UPDATE_DISPATCHERS: dict[str, ProfileUpdateCallable] = {
  "mssql": mssql.update_profile,
}

_UPDATE_IF_UNEDITED_DISPATCHERS: dict[str, ProfileUpdateIfUneditedCallable] = {
  "mssql": mssql.update_if_unedited,
}


def _validate_update_payload(payload: ProfileUpdateRequestPayload) -> None:
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
  payload: ProfileReadRequestPayload = dict(request.payload)
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
  payload: ProfileUpdateRequestPayload = dict(request.payload)
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
  payload: UpdateIfUneditedRequestPayload = dict(request.payload)
  result = await dispatcher(payload)
  return DBResponse(
    op=request.op,
    payload=result.payload,
    rowcount=result.rowcount,
  )
