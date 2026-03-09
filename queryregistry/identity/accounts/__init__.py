"""Identity accounts query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import AccountExistsRequestPayload

__all__ = ["account_exists_request"]


def account_exists_request(params: AccountExistsRequestPayload) -> DBRequest:
  return DBRequest(op="db:identity:accounts:exists:1", payload=dict(params))
