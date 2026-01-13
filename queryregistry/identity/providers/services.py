"""Identity providers query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateFromProviderCallable,
  GetAnyByProviderIdentifierCallable,
  GetByProviderIdentifierCallable,
  GetUserByEmailCallable,
  LinkProviderCallable,
  RelinkProviderCallable,
  SetProviderCallable,
  SoftDeleteAccountCallable,
  UnlinkLastProviderCallable,
  UnlinkProviderCallable,
)

__all__ = [
  "create_from_provider_v1",
  "get_any_by_provider_identifier_v1",
  "get_by_provider_identifier_v1",
  "get_user_by_email_v1",
  "link_provider_v1",
  "relink_provider_v1",
  "set_provider_v1",
  "soft_delete_account_v1",
  "unlink_last_provider_v1",
  "unlink_provider_v1",
]

_GET_BY_PROVIDER_IDENTIFIER_DISPATCHERS: dict[str, GetByProviderIdentifierCallable] = {
  "mssql": mssql.get_by_provider_identifier,
}

_GET_ANY_BY_PROVIDER_IDENTIFIER_DISPATCHERS: dict[str, GetAnyByProviderIdentifierCallable] = {
  "mssql": mssql.get_any_by_provider_identifier,
}

_GET_USER_BY_EMAIL_DISPATCHERS: dict[str, GetUserByEmailCallable] = {
  "mssql": mssql.get_user_by_email,
}

_CREATE_FROM_PROVIDER_DISPATCHERS: dict[str, CreateFromProviderCallable] = {
  "mssql": mssql.create_from_provider,
}

_LINK_PROVIDER_DISPATCHERS: dict[str, LinkProviderCallable] = {
  "mssql": mssql.link_provider,
}

_UNLINK_PROVIDER_DISPATCHERS: dict[str, UnlinkProviderCallable] = {
  "mssql": mssql.unlink_provider,
}

_UNLINK_LAST_PROVIDER_DISPATCHERS: dict[str, UnlinkLastProviderCallable] = {
  "mssql": mssql.unlink_last_provider,
}

_SET_PROVIDER_DISPATCHERS: dict[str, SetProviderCallable] = {
  "mssql": mssql.set_provider,
}

_RELINK_PROVIDER_DISPATCHERS: dict[str, RelinkProviderCallable] = {
  "mssql": mssql.relink_provider,
}

_SOFT_DELETE_ACCOUNT_DISPATCHERS: dict[str, SoftDeleteAccountCallable] = {
  "mssql": mssql.soft_delete_account,
}


async def get_by_provider_identifier_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _GET_BY_PROVIDER_IDENTIFIER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def get_any_by_provider_identifier_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _GET_ANY_BY_PROVIDER_IDENTIFIER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def get_user_by_email_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _GET_USER_BY_EMAIL_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def create_from_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _CREATE_FROM_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def link_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _LINK_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def unlink_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UNLINK_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def unlink_last_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UNLINK_LAST_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def set_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _SET_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def relink_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _RELINK_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)


async def soft_delete_account_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _SOFT_DELETE_ACCOUNT_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  result = await dispatcher(request.payload)
  return DBResponse(op=request.op, payload=result.payload)
