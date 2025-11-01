"""Public gallery query handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.queryregistry.models import DBRequest, DBResponse


async def handle_gallery_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  """Handle public gallery query requests."""

  raise NotImplementedError("Public gallery query handler not implemented yet")
