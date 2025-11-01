"""Finance domain handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.queryregistry.models import DBRequest, DBResponse


async def handle_finance_request(
  path: Sequence[str],
  request: DBRequest,
  provider: str,
) -> DBResponse:
  """Dispatch finance registry requests.

  This stub will be expanded with provider-specific logic.
  """
  raise NotImplementedError("Finance registry handler not implemented yet")
