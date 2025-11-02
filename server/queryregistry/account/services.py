"""Account query registry service dispatchers."""

from __future__ import annotations

from server.queryregistry.models import DBRequest, DBResponse
from server.queryregistry.types import CheckStatusCallable

from . import mssql

__all__ = ["account_check_status_v1"]

_PROVIDER_DISPATCHERS: dict[str, CheckStatusCallable] = {
  "mssql": mssql.check_status,
}


async def account_check_status_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for account registry")
  payload = await dispatcher()
  return DBResponse(op=request.op, payload=dict(payload))
