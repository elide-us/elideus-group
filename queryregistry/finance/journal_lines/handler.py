"""Finance journal lines subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import create_line_v1, create_lines_batch_v1, delete_by_journal_v1, list_by_journal_v1

__all__ = ["handle_journal_lines_request"]

DISPATCHERS = {
  ("list_by_journal", "1"): list_by_journal_v1,
  ("create_line", "1"): create_line_v1,
  ("create_lines_batch", "1"): create_lines_batch_v1,
  ("delete_by_journal", "1"): delete_by_journal_v1,
}


async def handle_journal_lines_request(
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
    detail="Unknown finance journal lines operation",
  )
