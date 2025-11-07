"""System configuration query registry service dispatchers."""

from __future__ import annotations

from server.queryregistry.models import DBRequest, DBResponse

from . import mssql
from ..models import SystemCheckStatusCallable

__all__ = ["system_check_status_v1"]

_PROVIDER_DISPATCHERS: dict[str, SystemCheckStatusCallable] = {
  "mssql": mssql.check_status,
}


async def system_check_status_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system configuration registry")
  payload = await dispatcher()
  return DBResponse(op=request.op, payload=dict(payload))
