"""Identity sessions query registry helpers."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import RotkeyLookupParams

__all__ = [
  "get_rotkey_request",
]


def get_rotkey_request(params: RotkeyLookupParams) -> DBRequest:
  payload = params.model_dump(exclude_none=True)
  return DBRequest(op="db:identity:sessions:get_rotkey:1", payload=payload)
