"""Identity profiles handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse
from .services import (
  read_profile_v1,
  update_profile_if_unedited_v1,
  update_profile_v1,
)

__all__ = ["handle_profiles_request"]

DISPATCHERS = {
  ("read", "1"): read_profile_v1,
  ("update", "1"): update_profile_v1,
  ("update_if_unedited", "1"): update_profile_if_unedited_v1,
}


async def handle_profiles_request(
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
    detail="Unknown identity profiles operation",
  )
