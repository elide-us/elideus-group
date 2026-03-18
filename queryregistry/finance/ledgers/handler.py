"""Finance ledgers query registry operation handler."""

from __future__ import annotations

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .services import (
  create_v1,
  delete_v1,
  get_by_name_v1,
  get_v1,
  journal_reference_count_v1,
  list_v1,
  update_v1,
)

__all__ = ["handle_ledgers_request"]

_DISPATCHERS = {
  ("create", "1"): create_v1,
  ("delete", "1"): delete_v1,
  ("get", "1"): get_v1,
  ("get_by_name", "1"): get_by_name_v1,
  ("journal_reference_count", "1"): journal_reference_count_v1,
  ("list", "1"): list_v1,
  ("update", "1"): update_v1,
}


async def handle_ledgers_request(
  path: list[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  key = tuple(path[:2])
  handler = _DISPATCHERS.get(key)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown finance ledgers registry operation")
  return await handler(request, provider=provider)
