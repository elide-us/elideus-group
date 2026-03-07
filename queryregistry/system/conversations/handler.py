"""System conversations handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  find_recent_v1,
  insert_conversation_v1,
  list_by_time_v1,
  list_recent_v1,
  update_output_v1,
)
from ..dispatch import SubdomainDispatcher

__all__ = ["handle_conversations_request"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("insert", "1"): insert_conversation_v1,
  ("find_recent", "1"): find_recent_v1,
  ("update_output", "1"): update_output_v1,
  ("list_by_time", "1"): list_by_time_v1,
  ("list_recent", "1"): list_recent_v1,
}


async def handle_conversations_request(
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
    detail="Unknown system conversations operation",
  )
