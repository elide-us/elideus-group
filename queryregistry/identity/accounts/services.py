"""Identity accounts query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import AccountExistsCallable, AccountsReadCallable, DiscordSecurityCallable

__all__ = [
  "account_exists_v1",
  "read_accounts_v1",
  "read_discord_security_v1",
]

_READ_DISPATCHERS: dict[str, AccountsReadCallable] = {
  "mssql": mssql.get_security_profile,
}

_EXISTS_DISPATCHERS: dict[str, AccountExistsCallable] = {
  "mssql": mssql.account_exists,
}


_DISCORD_SECURITY_DISPATCHERS: dict[str, DiscordSecurityCallable] = {
  "mssql": mssql.get_by_discord_id,
}


async def read_accounts_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _READ_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity accounts registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def account_exists_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _EXISTS_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity accounts registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def read_discord_security_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _DISCORD_SECURITY_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity accounts registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)
