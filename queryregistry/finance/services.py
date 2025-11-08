"""Finance query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import FinanceCheckStatusCallable

__all__ = ["finance_check_status_v1"]

_PROVIDER_DISPATCHERS: dict[str, FinanceCheckStatusCallable] = {
  "mssql": mssql.check_status,
}


async def finance_check_status_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance registry")
  payload = await dispatcher()
  return DBResponse(op=request.op, payload=dict(payload))
