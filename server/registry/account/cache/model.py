"""Pydantic models for content cache registry interactions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
  "CacheItemKey",
  "ContentCacheItem",
  "DeleteCacheFolderParams",
  "ListCacheParams",
  "ReplaceUserCacheParams",
  "SetPublicParams",
  "SetReportedParams",
  "UpsertCacheItemParams",
  "normalize_content_cache_item",
]


def _coerce_flag(value: Any) -> int:
  if value is None:
    return 0
  return 1 if bool(value) else 0


class ContentCacheItem(BaseModel):
  """Typed representation of a content cache row."""

  model_config = ConfigDict(extra="allow")

  user_guid: str
  filename: str
  path: str = ""
  content_type: str = "application/octet-stream"
  public: int = 0
  element_created_on: datetime | None = None
  element_modified_on: datetime | None = None
  url: str | None = None
  reported: int = 0
  moderation_recid: Any | None = None

  @model_validator(mode="before")
  @classmethod
  def _normalize(cls, value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, cls):
      return value.model_dump()
    if not isinstance(value, Mapping):
      raise TypeError("ContentCacheItem expects a mapping of values")
    data: MutableMapping[str, Any] = dict(value)
    user_guid = data.get("user_guid") or data.get("users_guid")
    if not user_guid:
      raise ValueError("user_guid is required for content cache items")
    data["user_guid"] = user_guid
    name = data.get("filename") or data.get("name")
    if name is None:
      raise ValueError("filename is required for content cache items")
    data["filename"] = name
    data["path"] = data.get("path") or ""
    data["content_type"] = data.get("content_type") or "application/octet-stream"
    data["public"] = _coerce_flag(data.get("public", 0))
    data["reported"] = _coerce_flag(data.get("reported", 0))
    if data.get("moderation_recid") == "":
      data["moderation_recid"] = None
    return data

  @classmethod
  def from_mapping(
    cls,
    data: Mapping[str, Any],
    *,
    default_user_guid: str | None = None,
  ) -> "ContentCacheItem":
    payload = dict(data)
    if default_user_guid and not payload.get("user_guid"):
      payload["user_guid"] = default_user_guid
    return cls.model_validate(payload)


  @field_validator("element_created_on", "element_modified_on", mode="before")
  @classmethod
  def _normalize_temporal_fields(cls, value: Any) -> datetime | None:
    if value is None or value == "":
      return None
    parsed = value
    if isinstance(parsed, str):
      candidate = parsed.strip()
      if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
      parsed = datetime.fromisoformat(candidate)
    if not isinstance(parsed, datetime):
      raise TypeError(f"Temporal field expects datetime-compatible value, got {type(parsed).__name__}")
    if parsed.tzinfo is None:
      return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

  def to_payload(self) -> dict[str, Any]:
    return self.model_dump()


class ListCacheParams(BaseModel):
  """Parameters required to list a user's cached items."""

  model_config = ConfigDict(extra="forbid")

  user_guid: str


class CacheItemKey(BaseModel):
  """Coordinates for identifying a cached item."""

  model_config = ConfigDict(extra="forbid")

  user_guid: str
  path: str = ""
  filename: str


class DeleteCacheFolderParams(BaseModel):
  """Parameters required to delete every item within a folder."""

  model_config = ConfigDict(extra="forbid")

  user_guid: str
  path: str = ""


class ReplaceUserCacheParams(BaseModel):
  """Payload used to replace a user's cache rows with provided items."""

  model_config = ConfigDict(extra="forbid")

  user_guid: str
  items: list[ContentCacheItem] = Field(default_factory=list)

  @model_validator(mode="before")
  @classmethod
  def _apply_defaults(cls, value: Any) -> Mapping[str, Any]:
    if isinstance(value, cls):
      return value.model_dump()
    if not isinstance(value, Mapping):
      raise TypeError("ReplaceUserCacheParams expects a mapping")
    data = dict(value)
    user_guid = data.get("user_guid")
    raw_items: Sequence[Any] = data.get("items", [])
    normalized: list[Any] = []
    for item in raw_items:
      if isinstance(item, Mapping):
        payload = dict(item)
        if user_guid and not payload.get("user_guid"):
          payload["user_guid"] = user_guid
        normalized.append(payload)
      else:
        normalized.append(item)
    data["items"] = normalized
    return data


class UpsertCacheItemParams(ContentCacheItem):
  """Validated payload for inserting or updating a cache item."""


class SetPublicParams(BaseModel):
  """Parameters used to toggle the public flag for a cached item."""

  model_config = ConfigDict(extra="forbid")

  user_guid: str
  public: bool
  name: str | None = None
  path: str | None = None
  filename: str | None = None


class SetReportedParams(CacheItemKey):
  """Parameters used to toggle the reported flag for a cached item."""

  reported: bool = True


def normalize_content_cache_item(
  item: Mapping[str, Any] | ContentCacheItem,
  *,
  default_user_guid: str | None = None,
) -> dict[str, Any]:
  """Normalize arbitrary cache data into the canonical payload shape."""

  if isinstance(item, ContentCacheItem):
    payload = item.model_dump()
  else:
    payload = dict(item)
  if default_user_guid and not payload.get("user_guid"):
    payload["user_guid"] = default_user_guid
  normalized = ContentCacheItem.model_validate(payload)
  return normalized.model_dump()
