"""Public users query handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.queryregistry.models import DBRequest, DBResponse


async def handle_users_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  """Handle public users query requests."""

  raise NotImplementedError("Public users query handler not implemented yet")
