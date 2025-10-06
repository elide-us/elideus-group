"""Security session registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "create_session_request",
  "register",
  "revoke_all_device_tokens_request",
  "revoke_device_token_request",
  "revoke_provider_tokens_request",
  "set_rotkey_request",
  "update_device_token_request",
  "update_session_request",
]


def _request(name: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:users:security.sessions:{name}:1", params=params)


def create_session_request(
  *,
  access_token: str,
  expires,
  fingerprint: str,
  user_guid: str,
  provider: str,
  user_agent: str | None = None,
  ip_address: str | None = None,
) -> DBRequest:
  params: dict[str, Any] = {
    "access_token": access_token,
    "expires": expires,
    "fingerprint": fingerprint,
    "user_guid": user_guid,
    "provider": provider,
  }
  if user_agent is not None:
    params["user_agent"] = user_agent
  if ip_address is not None:
    params["ip_address"] = ip_address
  return _request("create_session", params)


def update_session_request(
  *,
  access_token: str,
  user_agent: str | None,
  ip_address: str | None,
) -> DBRequest:
  params: dict[str, Any] = {
    "access_token": access_token,
    "user_agent": user_agent,
    "ip_address": ip_address,
  }
  return _request("update_session", params)


def update_device_token_request(*, device_guid: str, access_token: str) -> DBRequest:
  return _request(
    "update_device_token",
    {
      "device_guid": device_guid,
      "access_token": access_token,
    },
  )


def revoke_device_token_request(*, access_token: str) -> DBRequest:
  return _request("revoke_device_token", {"access_token": access_token})


def revoke_all_device_tokens_request(*, guid: str) -> DBRequest:
  return _request("revoke_all_device_tokens", {"guid": guid})


def revoke_provider_tokens_request(*, guid: str, provider: str) -> DBRequest:
  return _request(
    "revoke_provider_tokens",
    {
      "guid": guid,
      "provider": provider,
    },
  )


def set_rotkey_request(
  *,
  guid: str,
  rotkey: str,
  iat,
  exp,
) -> DBRequest:
  return _request(
    "set_rotkey",
    {
      "guid": guid,
      "rotkey": rotkey,
      "iat": iat,
      "exp": exp,
    },
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function("create_session", version=1)
  router.add_function("update_session", version=1)
  router.add_function("update_device_token", version=1)
  router.add_function("revoke_device_token", version=1)
  router.add_function("revoke_all_device_tokens", version=1)
  router.add_function("revoke_provider_tokens", version=1)
  router.add_function("set_rotkey", version=1)
