"""Account query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import AccountCheckStatusCallable

__all__ = ["account_check_status_v1"]

_PROVIDER_DISPATCHERS: dict[str, AccountCheckStatusCallable] = {
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
