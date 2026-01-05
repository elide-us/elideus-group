"""System public_vars handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import get_hostname_v1, get_repo_v1, get_version_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_public_vars_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get_version", "1"): get_version_v1,
  ("get_hostname", "1"): get_hostname_v1,
  ("get_repo", "1"): get_repo_v1,
}


async def handle_public_vars_request(
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
    detail="Unknown system public_vars operation",
  )
