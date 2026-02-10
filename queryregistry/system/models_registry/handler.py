"""System models handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse
from queryregistry.stubs import build_stub_dispatchers

__all__ = ["handle_models_request"]

DISPATCHERS = build_stub_dispatchers("system.models")


async def handle_models_request(
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
    detail="Unknown system models operation",
  )
