"""Content indexing handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  count_rows_v1,
  delete_folder_v1,
  delete_v1,
  get_published_files_v1,
  list_public_v1,
  list_reported_v1,
  list_v1,
  replace_user_v1,
  set_gallery_v1,
  set_public_v1,
  set_reported_v1,
  upsert_v1,
)

__all__ = ["handle_indexing_request"]

DISPATCHERS = {
  ("list", "1"): list_v1,
  ("list_public", "1"): list_public_v1,
  ("list_reported", "1"): list_reported_v1,
  ("replace_user", "1"): replace_user_v1,
  ("upsert", "1"): upsert_v1,
  ("delete", "1"): delete_v1,
  ("delete_folder", "1"): delete_folder_v1,
  ("set_public", "1"): set_public_v1,
  ("set_reported", "1"): set_reported_v1,
  ("count_rows", "1"): count_rows_v1,
  ("set_gallery", "1"): set_gallery_v1,
  ("get_published_files", "1"): get_published_files_v1,
}


async def handle_indexing_request(
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
    detail="Unknown content indexing operation",
  )
