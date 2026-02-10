"""Type contracts for system public user registry operations."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "GetProfileParams",
  "GetPublishedFilesParams",
  "PublicUserFile",
  "PublicUserProfile",
]


class GetProfileParams(TypedDict):
  """Parameters for fetching a public user profile."""

  guid: str


class GetPublishedFilesParams(TypedDict):
  """Parameters for retrieving published files for a user."""

  guid: str


class PublicUserProfile(TypedDict, total=False):
  """Public profile information returned for a user."""

  display_name: str | None
  email: str | None
  profile_image: str | None


class PublicUserFile(TypedDict):
  """Metadata describing a published user file."""

  path: str
  filename: str
  url: str
  content_type: str
