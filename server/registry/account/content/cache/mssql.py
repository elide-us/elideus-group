"""Compatibility proxy for cache MSSQL implementations."""

from server.registry.account.cache.mssql import (  # noqa: F401
  count_rows_v1,
  delete_folder_v1,
  delete_v1,
  list_public_v1,
  list_reported_v1,
  list_v1,
  replace_user_v1,
  set_public_v1,
  set_reported_v1,
  upsert_v1,
)
