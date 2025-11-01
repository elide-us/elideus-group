"""Public vars query handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.queryregistry.models import DBRequest, DBResponse


async def handle_vars_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  """Handle public vars query requests."""

  raise NotImplementedError("Public vars query handler not implemented yet")
