"""Data models for content cache operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

__all__ = [
  "ContentCacheItem",
  "normalize_content_cache_item",
]


def _coerce_flag(value: Any) -> int:
  if value is None:
    return 0
  return 1 if bool(value) else 0


def normalize_content_cache_item(item: Mapping[str, Any], *, default_user_guid: str | None = None) -> dict[str, Any]:
  data = dict(item)
  user_guid = data.get("user_guid") or default_user_guid
  if not user_guid:
    raise ValueError("user_guid is required for content cache items")
  data["user_guid"] = user_guid
  name = data.get("filename") or data.get("name")
  if name is None:
    raise ValueError("filename is required for content cache items")
  data["filename"] = name
  path = data.get("path")
  data["path"] = path or ""
  data.setdefault("content_type", "application/octet-stream")
  data["public"] = _coerce_flag(data.get("public", 0))
  data["reported"] = _coerce_flag(data.get("reported", 0))
  if "moderation_recid" in data and data["moderation_recid"] == "":
    data["moderation_recid"] = None
  return data


@dataclass(slots=True)
class ContentCacheItem:
  """Typed representation of a content cache row."""

  user_guid: str
  filename: str
  path: str = ""
  content_type: str = "application/octet-stream"
  public: int = 0
  created_on: Any | None = None
  modified_on: Any | None = None
  url: str | None = None
  reported: int = 0
  moderation_recid: Any | None = None

  @classmethod
  def from_mapping(cls, data: Mapping[str, Any]) -> "ContentCacheItem":
    normalized = normalize_content_cache_item(data)
    return cls(**normalized)

  def to_payload(self) -> dict[str, Any]:
    return normalize_content_cache_item({
      "user_guid": self.user_guid,
      "filename": self.filename,
      "path": self.path,
      "content_type": self.content_type,
      "public": self.public,
      "created_on": self.created_on,
      "modified_on": self.modified_on,
      "url": self.url,
      "reported": self.reported,
      "moderation_recid": self.moderation_recid,
    })
