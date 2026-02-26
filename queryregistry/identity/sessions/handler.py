"""Identity sessions handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_session_v1,
  get_rotkey_v1,
  list_snapshots_v1,
  read_sessions_v1,
  revoke_all_device_tokens_v1,
  revoke_device_token_v1,
  revoke_provider_tokens_v1,
  set_rotkey_v1,
  update_device_token_v1,
  update_session_v1,
)

__all__ = ["handle_sessions_request"]

DISPATCHERS = {
  ("read", "1"): read_sessions_v1,
  ("get_rotkey", "1"): get_rotkey_v1,
  ("create_session", "1"): create_session_v1,
  ("update_session", "1"): update_session_v1,
  ("update_device_token", "1"): update_device_token_v1,
  ("revoke_device_token", "1"): revoke_device_token_v1,
  ("revoke_all_device_tokens", "1"): revoke_all_device_tokens_v1,
  ("revoke_provider_tokens", "1"): revoke_provider_tokens_v1,
  ("set_rotkey", "1"): set_rotkey_v1,
  ("list_snapshots", "1"): list_snapshots_v1,
}


async def handle_sessions_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown identity sessions operation",
  )
