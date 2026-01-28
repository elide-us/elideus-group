"""Identity profiles query registry helpers."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import GuidParams, UpdateIfUneditedParams, UpdateProfileParams

__all__ = [
  "get_profile_request",
  "update_if_unedited_request",
  "update_profile_request",
]


def get_profile_request(params: GuidParams) -> DBRequest:
  return DBRequest(
    op="db:identity:profiles:read:1",
    payload=params.model_dump(),
  )


def update_profile_request(params: UpdateProfileParams) -> DBRequest:
  payload = params.model_dump(exclude_none=True)
  if params.provider is not None and "image_b64" not in payload:
    payload["image_b64"] = params.image_b64
  if params.display_email is not None:
    payload["display_email"] = 1 if params.display_email else 0
  return DBRequest(op="db:identity:profiles:update:1", payload=payload)


def update_if_unedited_request(params: UpdateIfUneditedParams) -> DBRequest:
  return DBRequest(
    op="db:identity:profiles:update_if_unedited:1",
    payload=params.model_dump(exclude_none=True),
  )
