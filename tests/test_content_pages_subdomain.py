"""Regression tests for content.pages QR subdomain and module API."""

import pytest
from pydantic import ValidationError

from queryregistry.content.pages import (
  create_page_request,
  create_version_request,
  delete_page_request,
  get_page_by_slug_request,
  get_page_request,
  get_version_request,
  list_pages_request,
  list_versions_request,
  update_page_request,
)
from queryregistry.content.pages.models import (
  CreatePageParams,
  CreateVersionParams,
  DeletePageParams,
  GetPageBySlugParams,
  GetPageParams,
  GetVersionParams,
  ListPagesParams,
  ListVersionsParams,
  UpdatePageParams,
)


class TestOpStringFormat:
  def test_pages_request_op_strings(self):
    requests = {
      "list": list_pages_request(ListPagesParams()),
      "get": get_page_request(GetPageParams(recid=1)),
      "get_by_slug": get_page_by_slug_request(GetPageBySlugParams(slug="home")),
      "create": create_page_request(
        CreatePageParams(
          slug="home",
          title="Home",
          content="<h1>Home</h1>",
          created_by="00000000-0000-0000-0000-000000000001",
        )
      ),
      "update": update_page_request(
        UpdatePageParams(
          recid=1,
          modified_by="00000000-0000-0000-0000-000000000001",
        )
      ),
      "delete": delete_page_request(
        DeletePageParams(
          recid=1,
          modified_by="00000000-0000-0000-0000-000000000001",
        )
      ),
      "create_version": create_version_request(
        CreateVersionParams(
          pages_recid=1,
          content="<p>v2</p>",
          created_by="00000000-0000-0000-0000-000000000001",
        )
      ),
      "list_versions": list_versions_request(ListVersionsParams(pages_recid=1)),
      "get_version": get_version_request(GetVersionParams(recid=1)),
    }

    for operation, request in requests.items():
      assert request.op == f"db:content:pages:{operation}:1"


class TestDispatcherKeys:
  def test_pages_dispatchers(self):
    from queryregistry.content.pages.handler import DISPATCHERS

    expected = {
      ("list", "1"),
      ("get", "1"),
      ("get_by_slug", "1"),
      ("create", "1"),
      ("update", "1"),
      ("delete", "1"),
      ("create_version", "1"),
      ("list_versions", "1"),
      ("get_version", "1"),
    }
    assert set(DISPATCHERS.keys()) == expected


class TestModelValidation:
  def test_create_page_required_fields(self):
    with pytest.raises(ValidationError):
      CreatePageParams(title="Home", content="x", created_by="00000000-0000-0000-0000-000000000001")
    with pytest.raises(ValidationError):
      CreatePageParams(slug="home", content="x", created_by="00000000-0000-0000-0000-000000000001")
    with pytest.raises(ValidationError):
      CreatePageParams(slug="home", title="Home", created_by="00000000-0000-0000-0000-000000000001")
    with pytest.raises(ValidationError):
      CreatePageParams(slug="home", title="Home", content="x")

  def test_get_page_by_slug_requires_slug(self):
    with pytest.raises(ValidationError):
      GetPageBySlugParams()

  def test_update_page_requires_recid_and_modified_by(self):
    with pytest.raises(ValidationError):
      UpdatePageParams(modified_by="00000000-0000-0000-0000-000000000001")
    with pytest.raises(ValidationError):
      UpdatePageParams(recid=1)


class TestModelRejection:
  def test_extra_fields_rejected(self):
    with pytest.raises(ValidationError):
      ListPagesParams(unexpected=True)
    with pytest.raises(ValidationError):
      GetPageParams(recid=1, unexpected=True)
    with pytest.raises(ValidationError):
      CreateVersionParams(
        pages_recid=1,
        content="x",
        created_by="00000000-0000-0000-0000-000000000001",
        unexpected=True,
      )


class TestImportPaths:
  def test_import_from_pages_package(self):
    from queryregistry.content.pages import (
      create_page_request,
      create_version_request,
      delete_page_request,
      get_page_by_slug_request,
      get_page_request,
      get_version_request,
      list_pages_request,
      list_versions_request,
      update_page_request,
    )

    assert callable(list_pages_request)
    assert callable(get_page_request)
    assert callable(get_page_by_slug_request)
    assert callable(create_page_request)
    assert callable(update_page_request)
    assert callable(delete_page_request)
    assert callable(create_version_request)
    assert callable(list_versions_request)
    assert callable(get_version_request)

  def test_import_from_pages_models(self):
    from queryregistry.content.pages.models import (
      CreatePageParams,
      CreateVersionParams,
      DeletePageParams,
      GetPageBySlugParams,
      GetPageParams,
      GetVersionParams,
      ListPagesParams,
      ListVersionsParams,
      PageRecord,
      PageWithContentRecord,
      UpdatePageParams,
      VersionRecord,
    )

    assert CreatePageParams is not None
    assert UpdatePageParams is not None
    assert GetPageParams is not None
    assert GetPageBySlugParams is not None
    assert DeletePageParams is not None
    assert CreateVersionParams is not None
    assert ListVersionsParams is not None
    assert GetVersionParams is not None
    assert ListPagesParams is not None
    assert PageRecord is not None
    assert PageWithContentRecord is not None
    assert VersionRecord is not None


class TestModuleImport:
  def test_content_pages_module_importable(self):
    from server.modules.content_pages_module import ContentPagesModule

    assert ContentPagesModule is not None

  def test_content_pages_module_interface(self):
    from server.modules.content_pages_module import ContentPagesModule

    expected_methods = [
      "list_pages",
      "get_page",
      "get_page_by_slug",
      "create_page",
      "update_page",
      "delete_page",
      "create_version",
      "list_versions",
      "get_version",
    ]

    for method in expected_methods:
      assert hasattr(ContentPagesModule, method)
