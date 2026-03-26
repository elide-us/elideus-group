"""Identity auth handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_from_provider_v1,
  get_any_by_provider_identifier_v1,
  get_by_provider_identifier_v1,
  get_user_by_email_v1,
  link_provider_v1,
  relink_provider_v1,
  set_provider_v1,
  soft_delete_account_v1,
  unlink_last_provider_v1,
  unlink_provider_v1,
)

__all__ = ["handle_auth_request"]

DISPATCHERS = {
  ("get_by_provider_identifier", "1"): get_by_provider_identifier_v1,
  ("get_any_by_provider_identifier", "1"): get_any_by_provider_identifier_v1,
  ("get_user_by_email", "1"): get_user_by_email_v1,
  ("create_from_provider", "1"): create_from_provider_v1,
  ("link_provider", "1"): link_provider_v1,
  ("unlink_provider", "1"): unlink_provider_v1,
  ("unlink_last_provider", "1"): unlink_last_provider_v1,
  ("set_provider", "1"): set_provider_v1,
  ("relink", "1"): relink_provider_v1,
  ("soft_delete_account", "1"): soft_delete_account_v1,
}


async def handle_auth_request(
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
    detail="Unknown identity auth operation",
  )
