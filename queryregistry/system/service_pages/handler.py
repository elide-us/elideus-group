"""System service_pages handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse
from queryregistry.stubs import build_stub_dispatchers

__all__ = ["handle_service_pages_request"]

DISPATCHERS = build_stub_dispatchers("system.service_pages")


async def handle_service_pages_request(
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
    detail="Unknown system service_pages operation",
  )
