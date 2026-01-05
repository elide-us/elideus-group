"""Compatibility proxy for cache model definitions."""

from server.registry.account.cache.model import (  # noqa: F401
  CacheItemKey,
  ContentCacheItem,
  DeleteCacheFolderParams,
  ListCacheParams,
  ReplaceUserCacheParams,
  SetPublicParams,
  SetReportedParams,
  UpsertCacheItemParams,
  normalize_content_cache_item,
)
