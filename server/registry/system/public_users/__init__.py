"""Public users registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

from .model import (
  GetProfileParams,
  GetPublishedFilesParams,
  PublicUserFile,
  PublicUserProfile,
)

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "GetProfileParams",
  "GetPublishedFilesParams",
  "PublicUserFile",
  "PublicUserProfile",
  "get_profile_request",
  "get_published_files_request",
  "register",
]


def _request(op: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=op, payload=params)


def get_profile_request(*, guid: str) -> DBRequest:
  params: GetProfileParams = {"guid": guid}
  return _request("db:system:public_users:get_profile:1", params)


def get_published_files_request(*, guid: str) -> DBRequest:
  params: GetPublishedFilesParams = {"guid": guid}
  return _request("db:system:public_users:get_published_files:1", params)


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_profile", version=1)
  router.add_function("get_published_files", version=1)
