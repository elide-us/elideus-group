"""Security identity linkage registry helpers."""

from __future__ import annotations

from server.registry.types import DBRequest
from .model import (
  CreateFromProviderParams,
  GetUserByEmailParams,
  LinkProviderParams,
  ProviderIdentifierParams,
  SetProviderParams,
  UnlinkLastProviderParams,
  UnlinkProviderParams,
)

def _request(op: str, params: dict[str, object]) -> DBRequest:
  return DBRequest(op=op, payload=params)


def create_from_provider_request(params: CreateFromProviderParams) -> DBRequest:
  payload = params.model_dump()
  if payload.get("provider_profile_image") is None:
    payload["provider_profile_image"] = ""
  return _request("db:account:providers:create_from_provider:1", payload)


def get_by_provider_identifier_request(params: ProviderIdentifierParams) -> DBRequest:
  return _request(
    "db:account:providers:get_by_provider_identifier:1",
    params.model_dump(),
  )


def get_any_by_provider_identifier_request(params: ProviderIdentifierParams) -> DBRequest:
  return _request(
    "db:account:providers:get_any_by_provider_identifier:1",
    params.model_dump(),
  )


def get_user_by_email_request(params: GetUserByEmailParams) -> DBRequest:
  return _request(
    "db:account:providers:get_user_by_email:1",
    params.model_dump(),
  )


def link_provider_request(params: LinkProviderParams) -> DBRequest:
  return _request(
    "db:account:providers:link_provider:1",
    params.model_dump(),
  )


def set_provider_request(params: SetProviderParams) -> DBRequest:
  return _request(
    "db:account:providers:set_provider:1",
    params.model_dump(),
  )


def unlink_provider_request(params: UnlinkProviderParams) -> DBRequest:
  payload = params.model_dump(exclude_none=True)
  return _request("db:account:providers:unlink_provider:1", payload)


def unlink_last_provider_request(params: UnlinkLastProviderParams) -> DBRequest:
  return _request(
    "db:account:providers:unlink_last_provider:1",
    params.model_dump(),
  )
