"""Account domain handler stubs."""

from __future__ import annotations

from typing import Sequence

from server.registry.models import DBRequest, DBResponse


async def handle_account_request(
  path: Sequence[str],
  request: DBRequest,
  provider: str,
) -> DBResponse:
  """Dispatch account registry requests.

  This stub will be expanded with provider-specific logic.
  """
  raise NotImplementedError("Account registry handler not implemented yet")
