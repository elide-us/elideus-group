"""Identity auth query registry helpers."""

from __future__ import annotations

from typing import Any

from queryregistry.models import DBRequest

__all__ = [
  "create_from_provider_request",
  "get_any_by_provider_identifier_request",
  "get_by_provider_identifier_request",
  "get_user_by_email_request",
  "link_provider_request",
  "relink_provider_request",
  "set_provider_request",
  "soft_delete_account_request",
  "unlink_last_provider_request",
  "unlink_provider_request",
]


def get_by_provider_identifier_request(
  *,
  provider: str,
  provider_identifier: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:get_by_provider_identifier:1",
    payload={
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def get_any_by_provider_identifier_request(
  *,
  provider_identifier: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:get_any_by_provider_identifier:1",
    payload={
      "provider_identifier": provider_identifier,
    },
  )


def get_user_by_email_request(
  *,
  email: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:get_user_by_email:1",
    payload={"email": email},
  )


def create_from_provider_request(
  *,
  provider: str,
  provider_identifier: str,
  email: str,
  displayname: str,
  profile_image: str | None = None,
) -> DBRequest:
  payload: dict[str, Any] = {
    "provider": provider,
    "provider_identifier": provider_identifier,
    "email": email,
    "displayname": displayname,
  }
  if profile_image is not None:
    payload["profile_image"] = profile_image
  return DBRequest(op="db:identity:auth:create_from_provider:1", payload=payload)


def link_provider_request(
  *,
  guid: str,
  provider: str,
  provider_identifier: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:link_provider:1",
    payload={
      "guid": guid,
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def unlink_provider_request(
  *,
  guid: str,
  provider: str,
  new_provider_recid: int | None = None,
) -> DBRequest:
  payload: dict[str, Any] = {
    "guid": guid,
    "provider": provider,
  }
  if new_provider_recid is not None:
    payload["new_provider_recid"] = new_provider_recid
  return DBRequest(op="db:identity:auth:unlink_provider:1", payload=payload)


def unlink_last_provider_request(
  *,
  guid: str,
  provider: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:unlink_last_provider:1",
    payload={
      "guid": guid,
      "provider": provider,
    },
  )


def set_provider_request(
  *,
  guid: str,
  provider: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:set_provider:1",
    payload={
      "guid": guid,
      "provider": provider,
    },
  )


def relink_provider_request(
  *,
  provider: str,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  payload: dict[str, Any] = {
    "provider": provider,
    "provider_identifier": provider_identifier,
    "email": email,
    "display_name": display_name,
  }
  if profile_image is not None:
    payload["profile_image"] = profile_image
  if confirm is not None:
    payload["confirm"] = confirm
  if reauth_token is not None:
    payload["reauth_token"] = reauth_token
  return DBRequest(op="db:identity:auth:relink:1", payload=payload)


def soft_delete_account_request(
  *,
  guid: str,
) -> DBRequest:
  return DBRequest(
    op="db:identity:auth:soft_delete_account:1",
    payload={"guid": guid},
  )
