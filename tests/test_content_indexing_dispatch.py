"""Regression tests for content.indexing QR subdomain dispatch.

Validates that the content domain correctly routes indexing operations
after the cache → indexing rename migration.
"""

from queryregistry.content.handler import HANDLERS
from queryregistry.content.indexing import (
  count_rows_request,
  delete_cache_folder_request,
  delete_cache_item_request,
  get_published_files_request,
  list_cache_request,
  list_public_request,
  list_reported_request,
  replace_user_cache_request,
  set_gallery_request,
  set_reported_request,
  upsert_cache_item_request,
)
from queryregistry.content.indexing.models import (
  CacheItemKey,
  DeleteCacheFolderParams,
  GetPublishedFilesParams,
  ListCacheParams,
  ReplaceUserCacheParams,
  SetGalleryParams,
  SetReportedParams,
  UpsertCacheItemParams,
)


class TestOpStringFormat:
  """Verify all request builders produce db:content:indexing:*:1 op strings."""

  def test_list_cache_request_op(self):
    req = list_cache_request(ListCacheParams(user_guid="00000000-0000-0000-0000-000000000001"))
    assert req.op == "db:content:indexing:list:1"

  def test_list_public_request_op(self):
    req = list_public_request()
    assert req.op == "db:content:indexing:list_public:1"

  def test_list_reported_request_op(self):
    req = list_reported_request()
    assert req.op == "db:content:indexing:list_reported:1"

  def test_upsert_cache_item_request_op(self):
    req = upsert_cache_item_request(
      UpsertCacheItemParams(
        user_guid="00000000-0000-0000-0000-000000000001",
        filename="test.png",
      )
    )
    assert req.op == "db:content:indexing:upsert:1"

  def test_delete_cache_item_request_op(self):
    req = delete_cache_item_request(
      CacheItemKey(
        user_guid="00000000-0000-0000-0000-000000000001",
        filename="test.png",
      )
    )
    assert req.op == "db:content:indexing:delete:1"

  def test_delete_cache_folder_request_op(self):
    req = delete_cache_folder_request(
      DeleteCacheFolderParams(
        user_guid="00000000-0000-0000-0000-000000000001",
      )
    )
    assert req.op == "db:content:indexing:delete_folder:1"

  def test_replace_user_cache_request_op(self):
    req = replace_user_cache_request(
      ReplaceUserCacheParams(
        user_guid="00000000-0000-0000-0000-000000000001",
        items=[],
      )
    )
    assert req.op == "db:content:indexing:replace_user:1"

  def test_set_reported_request_op(self):
    req = set_reported_request(
      SetReportedParams(
        user_guid="00000000-0000-0000-0000-000000000001",
        filename="test.png",
        reported=True,
      )
    )
    assert req.op == "db:content:indexing:set_reported:1"

  def test_set_gallery_request_op(self):
    req = set_gallery_request(
      SetGalleryParams(
        user_guid="00000000-0000-0000-0000-000000000001",
        gallery=True,
      )
    )
    assert req.op == "db:content:indexing:set_gallery:1"

  def test_count_rows_request_op(self):
    req = count_rows_request()
    assert req.op == "db:content:indexing:count_rows:1"

  def test_get_published_files_request_op(self):
    req = get_published_files_request(GetPublishedFilesParams(guid="00000000-0000-0000-0000-000000000001"))
    assert req.op == "db:content:indexing:get_published_files:1"


class TestNoLegacyOpStrings:
  """Verify no request builder produces the old db:content:cache:* op format."""

  def test_no_cache_op_strings(self):
    all_requests = [
      list_cache_request(ListCacheParams(user_guid="00000000-0000-0000-0000-000000000001")),
      list_public_request(),
      list_reported_request(),
      upsert_cache_item_request(
        UpsertCacheItemParams(
          user_guid="00000000-0000-0000-0000-000000000001",
          filename="test.png",
        )
      ),
      delete_cache_item_request(
        CacheItemKey(
          user_guid="00000000-0000-0000-0000-000000000001",
          filename="test.png",
        )
      ),
      delete_cache_folder_request(
        DeleteCacheFolderParams(
          user_guid="00000000-0000-0000-0000-000000000001",
        )
      ),
      replace_user_cache_request(
        ReplaceUserCacheParams(
          user_guid="00000000-0000-0000-0000-000000000001",
          items=[],
        )
      ),
      count_rows_request(),
      set_gallery_request(
        SetGalleryParams(
          user_guid="00000000-0000-0000-0000-000000000001",
          gallery=True,
        )
      ),
      get_published_files_request(GetPublishedFilesParams(guid="00000000-0000-0000-0000-000000000001")),
    ]
    for req in all_requests:
      assert "db:content:cache:" not in req.op, f"Legacy op string found: {req.op}"
      assert req.op.startswith("db:content:indexing:"), f"Wrong prefix: {req.op}"


class TestContentDomainHandlerRouting:
  """Verify the content domain handler routes to indexing subdomain."""

  def test_indexing_in_handlers(self):
    assert "indexing" in HANDLERS, "indexing subdomain not registered in content HANDLERS"

  def test_cache_stub_in_handlers(self):
    assert "cache" in HANDLERS, "cache stub subdomain not registered in content HANDLERS"

  def test_no_legacy_stubs_in_handlers(self):
    for name in ("assets", "galleries", "moderation", "visibility"):
      assert name not in HANDLERS, f"Legacy stub '{name}' still in content HANDLERS"


class TestContentIndexingDispatcherKeys:
  """Verify the indexing handler dispatcher map has all expected operations."""

  def test_all_dispatchers_present(self):
    from queryregistry.content.indexing.handler import DISPATCHERS

    expected = {
      ("list", "1"),
      ("list_public", "1"),
      ("list_reported", "1"),
      ("replace_user", "1"),
      ("upsert", "1"),
      ("delete", "1"),
      ("delete_folder", "1"),
      ("set_public", "1"),
      ("set_reported", "1"),
      ("count_rows", "1"),
      ("set_gallery", "1"),
      ("get_published_files", "1"),
    }
    assert set(DISPATCHERS.keys()) == expected


class TestModelImportPaths:
  """Verify models are importable from the new path."""

  def test_import_models(self):
    from queryregistry.content.indexing.models import (
      CacheItemKey,
      ContentCacheItem,
      DeleteCacheFolderParams,
      GetPublishedFilesParams,
      ListCacheParams,
      ReplaceUserCacheParams,
      SetGalleryParams,
      SetPublicParams,
      SetReportedParams,
      UpsertCacheItemParams,
      normalize_content_cache_item,
    )

    assert CacheItemKey is not None
    assert ContentCacheItem is not None
    assert normalize_content_cache_item is not None

  def test_import_request_builders(self):
    from queryregistry.content.indexing import (
      count_rows_request,
      delete_cache_folder_request,
      delete_cache_item_request,
      get_published_files_request,
      list_cache_request,
      list_public_request,
      list_reported_request,
      replace_user_cache_request,
      set_gallery_request,
      set_reported_request,
      upsert_cache_item_request,
    )

    assert callable(list_cache_request)
    assert callable(upsert_cache_item_request)
