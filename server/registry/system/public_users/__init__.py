"""Public users registry bindings."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBRequest

from .model import (
  GetProfileParams,
  GetPublishedFilesParams,
  PublicUserFile,
  PublicUserProfile,
)



def _request(op: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=op, payload=params)


def get_profile_request(*, guid: str) -> DBRequest:
  params: GetProfileParams = {"guid": guid}
  return _request("db:system:public_users:get_profile:1", params)


def get_published_files_request(*, guid: str) -> DBRequest:
  params: GetPublishedFilesParams = {"guid": guid}
  return _request("db:system:public_users:get_published_files:1", params)
