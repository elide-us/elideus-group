"""Account OAuth registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "relink_discord_request",
  "relink_google_request",
  "relink_microsoft_request",
  "register",
]


def _relink_request(name: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:account:oauth:{name}:1", payload=params)


def _common_params(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "provider_identifier": provider_identifier,
    "email": email,
    "display_name": display_name,
    "profile_image": profile_image or "",
  }
  if confirm is not None:
    payload["confirm"] = confirm
  if reauth_token is not None:
    payload["reauth_token"] = reauth_token
  return payload


def relink_discord_request(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  return _relink_request(
    "relink_discord",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def relink_google_request(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  return _relink_request(
    "relink_google",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def relink_microsoft_request(
  *,
  provider_identifier: str,
  email: str,
  display_name: str,
  profile_image: str | None = None,
  confirm: bool | None = None,
  reauth_token: str | None = None,
) -> DBRequest:
  return _relink_request(
    "relink_microsoft",
    _common_params(
      provider_identifier=provider_identifier,
      email=email,
      display_name=display_name,
      profile_image=profile_image,
      confirm=confirm,
      reauth_token=reauth_token,
    ),
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function("relink_discord", version=1)
  router.add_function("relink_google", version=1)
  router.add_function("relink_microsoft", version=1)
