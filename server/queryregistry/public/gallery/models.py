"""Public gallery query registry service models."""

from __future__ import annotations

from typing import TypedDict

from server.queryregistry.types import CheckStatusCallable

__all__ = [
  "PublicGalleryCheckStatusCallable",
  "PublicGalleryCheckStatusPayload",
]


class PublicGalleryCheckStatusPayload(TypedDict):
  status: str
  provider: str


PublicGalleryCheckStatusCallable = CheckStatusCallable
