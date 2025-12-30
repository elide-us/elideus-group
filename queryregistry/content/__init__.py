"""Content query registry namespace."""

from __future__ import annotations

from .assets.handler import handle_assets_request
from .cache.handler import handle_cache_request
from .galleries.handler import handle_galleries_request
from .moderation.handler import handle_moderation_request
from .visibility.handler import handle_visibility_request

__all__ = ["HANDLERS"]

HANDLERS = {
  "assets": handle_assets_request,
  "cache": handle_cache_request,
  "galleries": handle_galleries_request,
  "moderation": handle_moderation_request,
  "visibility": handle_visibility_request,
}
