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
  "unlink_last_provider_request",
  "unlink_provider_request",
]

_DEF_PROVIDER = "security.identities"
_PROVIDER_MODULE = "server.registry.security.identities.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "create_from_provider": "create_from_provider_v1",
  "get_any_by_provider_identifier": "get_any_by_provider_identifier_v1",
  "get_by_provider_identifier": "get_by_provider_identifier_v1",
  "get_user_by_email": "get_user_by_email_v1",
  "link_provider": "link_provider_v1",
  "set_provider": "set_provider_v1",
  "soft_delete_account": "soft_delete_account_v1",
  "unlink_last_provider": "unlink_last_provider_v1",
  "unlink_provider": "unlink_provider_v1",
}


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
    "db:security:identities:create_from_provider:1",
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
    "db:security:identities:get_by_provider_identifier:1",
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
    "db:security:identities:get_any_by_provider_identifier:1",
    {
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def get_user_by_email_request(*, email: str) -> DBRequest:
  return _request(
    "db:security:identities:get_user_by_email:1",
    {"email": email},
  )


def link_provider_request(
  *,
  guid: str,
  provider: str,
  provider_identifier: str,
) -> DBRequest:
  return _request(
    "db:security:identities:link_provider:1",
    {
      "guid": guid,
      "provider": provider,
      "provider_identifier": provider_identifier,
    },
  )


def set_provider_request(*, guid: str, provider: str) -> DBRequest:
  return _request(
    "db:security:identities:set_provider:1",
    {
      "guid": guid,
      "provider": provider,
    },
  )


def soft_delete_account_request(*, guid: str) -> DBRequest:
  return _request(
    "db:security:identities:soft_delete_account:1",
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
  return _request("db:security:identities:unlink_provider:1", params)


def unlink_last_provider_request(*, guid: str, provider: str) -> DBRequest:
  return _request(
    "db:security:identities:unlink_last_provider:1",
    {
      "guid": guid,
      "provider": provider,
    },
  )


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
