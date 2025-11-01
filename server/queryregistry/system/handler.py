"""System domain handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.queryregistry.models import DBRequest, DBResponse


async def handle_system_request(
  path: Sequence[str],
  request: DBRequest,
  provider: str,
) -> DBResponse:
  """Dispatch system registry requests.

  This stub will be expanded with provider-specific logic.
  """
  raise NotImplementedError("System registry handler not implemented yet")
