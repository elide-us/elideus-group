"""Public links query handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.queryregistry.models import DBRequest, DBResponse


async def handle_links_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  """Handle public links query requests."""

  raise NotImplementedError("Public links query handler not implemented yet")
