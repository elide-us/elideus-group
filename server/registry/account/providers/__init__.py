"""Security identity linkage registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "create_from_provider_request",
  "get_any_by_provider_identifier_request",
  "get_by_provider_identifier_request",
  "get_user_by_email_request",
  "link_provider_request",
  "register",
  "set_provider_request",
  "soft_delete_account_request",
  "unlink_provider_request",
  "unlink_last_provider_request",
]


def _request(op: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=op, params=params)


def create_from_provider_request(
  *,
  provider: str,
  provider_identifier: str,
  provider_email: str,
  provider_displayname: str,
  provider_profile_image: str | None = None,
) -> DBRequest:
  return _request(
    "db:account:providers:create_from_provider:1",
    {
      "provider": provider,
      "provider_identifier": provider_identifier,
      "provider_email": provider_email,
      "provider_displayname": provider_displayname,
      "provider_profile_image": provider_profile_image or "",
    },
  )


def get_by_provider_identifier_request(
  *,
  provider: str,
  provider_identifier: str,
) -> DBRequest:
  return _request(
    "db:account:providers:get_by_provider_identifier:1",
    {
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def get_any_by_provider_identifier_request(
  *,
  provider: str,
  provider_identifier: str,
) -> DBRequest:
  return _request(
    "db:account:providers:get_any_by_provider_identifier:1",
    {
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def get_user_by_email_request(*, email: str) -> DBRequest:
  return _request(
    "db:account:providers:get_user_by_email:1",
    {"email": email},
  )


def link_provider_request(
  *,
  guid: str,
  provider: str,
  provider_identifier: str,
) -> DBRequest:
  return _request(
    "db:account:providers:link_provider:1",
    {
      "guid": guid,
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def set_provider_request(*, guid: str, provider: str) -> DBRequest:
  return _request(
    "db:account:providers:set_provider:1",
    {
      "guid": guid,
      "provider": provider,
    },
  )


def soft_delete_account_request(*, guid: str) -> DBRequest:
  return _request(
    "db:account:providers:soft_delete_account:1",
    {"guid": guid},
  )


def unlink_provider_request(
  *,
  guid: str,
  provider: str,
  new_provider_recid: int | None = None,
) -> DBRequest:
  params: dict[str, Any] = {
    "guid": guid,
    "provider": provider,
  }
  if new_provider_recid is not None:
    params["new_provider_recid"] = new_provider_recid
  return _request("db:account:providers:unlink_provider:1", params)


def unlink_last_provider_request(*, guid: str, provider: str) -> DBRequest:
  return _request(
    "db:account:providers:unlink_last_provider:1",
    {
      "guid": guid,
      "provider": provider,
    },
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function("create_from_provider", version=1)
  router.add_function("get_any_by_provider_identifier", version=1)
  router.add_function("get_by_provider_identifier", version=1)
  router.add_function("get_user_by_email", version=1)
  router.add_function("link_provider", version=1)
  router.add_function("set_provider", version=1)
  router.add_function("soft_delete_account", version=1)
  router.add_function("unlink_provider", version=1)
  router.add_function("unlink_last_provider", version=1)
