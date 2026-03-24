"""Identity providers query registry service dispatchers."""

from __future__ import annotations

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateFromProviderParams,
  GetAnyByProviderIdentifierParams,
  ProviderIdentifierParams,
  GetUserByEmailParams,
  LinkProviderParams,
  SetProviderParams,
  UnlinkLastProviderParams,
  UnlinkProviderParams,
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

_GET_BY_PROVIDER_IDENTIFIER_DISPATCHERS = {
  "mssql": mssql.get_by_provider_identifier_v1,
}

_GET_ANY_BY_PROVIDER_IDENTIFIER_DISPATCHERS = {
  "mssql": mssql.get_any_by_provider_identifier_v1,
}

_GET_USER_BY_EMAIL_DISPATCHERS = {
  "mssql": mssql.get_user_by_email_v1,
}

_CREATE_FROM_PROVIDER_DISPATCHERS = {
  "mssql": mssql.create_from_provider_v1,
}

_LINK_PROVIDER_DISPATCHERS = {
  "mssql": mssql.link_provider_v1,
}

_UNLINK_PROVIDER_DISPATCHERS = {
  "mssql": mssql.unlink_provider_v1,
}

_UNLINK_LAST_PROVIDER_DISPATCHERS = {
  "mssql": mssql.unlink_last_provider_v1,
}

_SET_PROVIDER_DISPATCHERS = {
  "mssql": mssql.set_provider_v1,
}

_RELINK_PROVIDER_DISPATCHERS = {
  "mssql": mssql.relink_provider,
}

_SOFT_DELETE_ACCOUNT_DISPATCHERS = {
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
  params = ProviderIdentifierParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_any_by_provider_identifier_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _GET_ANY_BY_PROVIDER_IDENTIFIER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = GetAnyByProviderIdentifierParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_user_by_email_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _GET_USER_BY_EMAIL_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = GetUserByEmailParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_from_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _CREATE_FROM_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = CreateFromProviderParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def link_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _LINK_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = LinkProviderParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def unlink_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UNLINK_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = UnlinkProviderParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump(exclude_none=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def unlink_last_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _UNLINK_LAST_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = UnlinkLastProviderParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def set_provider_v1(
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  dispatcher = _SET_PROVIDER_DISPATCHERS.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for identity providers registry")
  params = SetProviderParams.model_validate(request.payload)
  result = await dispatcher(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


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
