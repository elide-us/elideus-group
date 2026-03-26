from __future__ import annotations

import importlib

import pytest
from pydantic import ValidationError

from queryregistry.content.wiki import (
  create_version_request,
  create_wiki_request,
  delete_wiki_request,
  get_version_request,
  get_wiki_by_route_context_request,
  get_wiki_by_slug_request,
  get_wiki_request,
  list_children_request,
  list_versions_request,
  list_wiki_request,
  update_wiki_request,
)
from queryregistry.content.wiki.handler import DISPATCHERS as QR_WIKI_DISPATCHERS
from queryregistry.content.wiki.models import (
  CreateWikiParams,
  CreateWikiVersionParams,
  DeleteWikiParams,
  GetWikiByRouteContextParams,
  GetWikiBySlugParams,
  GetWikiParams,
  GetWikiVersionParams,
  ListChildrenParams,
  ListWikiParams,
  ListWikiVersionsParams,
  UpdateWikiParams,
)
from rpc.public import HANDLERS as PUBLIC_HANDLERS
from rpc.users import HANDLERS as USERS_HANDLERS


@pytest.mark.parametrize(
  ("builder", "params", "expected_op"),
  [
    (list_wiki_request, ListWikiParams(), "db:content:wiki:list:1"),
    (get_wiki_request, GetWikiParams(recid=1), "db:content:wiki:get:1"),
    (get_wiki_by_slug_request, GetWikiBySlugParams(slug="home"), "db:content:wiki:get_by_slug:1"),
    (
      get_wiki_by_route_context_request,
      GetWikiByRouteContextParams(route_context="guidepanel.finance"),
      "db:content:wiki:get_by_route_context:1",
    ),
    (list_children_request, ListChildrenParams(parent_slug="home"), "db:content:wiki:list_children:1"),
    (
      create_wiki_request,
      CreateWikiParams(slug="home", title="Home", content="Body", created_by="00000000-0000-0000-0000-000000000000"),
      "db:content:wiki:create:1",
    ),
    (
      update_wiki_request,
      UpdateWikiParams(recid=1, modified_by="00000000-0000-0000-0000-000000000000"),
      "db:content:wiki:update:1",
    ),
    (
      delete_wiki_request,
      DeleteWikiParams(recid=1, modified_by="00000000-0000-0000-0000-000000000000"),
      "db:content:wiki:delete:1",
    ),
    (
      create_version_request,
      CreateWikiVersionParams(
        wiki_recid=1,
        content="Body",
        created_by="00000000-0000-0000-0000-000000000000",
      ),
      "db:content:wiki:create_version:1",
    ),
    (
      list_versions_request,
      ListWikiVersionsParams(wiki_recid=1),
      "db:content:wiki:list_versions:1",
    ),
    (
      get_version_request,
      GetWikiVersionParams(wiki_recid=1, version=1),
      "db:content:wiki:get_version:1",
    ),
  ],
)
def test_wiki_request_builders_emit_expected_ops(builder, params, expected_op):
  request = builder(params)
  assert request.op == expected_op


def test_wiki_handler_dispatcher_contains_expected_operations():
  expected = {
    ("list", "1"),
    ("get", "1"),
    ("get_by_slug", "1"),
    ("get_by_route_context", "1"),
    ("list_children", "1"),
    ("create", "1"),
    ("update", "1"),
    ("delete", "1"),
    ("create_version", "1"),
    ("list_versions", "1"),
    ("get_version", "1"),
  }
  assert set(QR_WIKI_DISPATCHERS.keys()) == expected
  assert len(QR_WIKI_DISPATCHERS) == 11


def test_create_wiki_params_required_fields():
  with pytest.raises(ValidationError):
    CreateWikiParams.model_validate({"title": "Home", "content": "body", "created_by": "x"})

  with pytest.raises(ValidationError):
    CreateWikiParams.model_validate({"slug": "home", "content": "body", "created_by": "x"})

  with pytest.raises(ValidationError):
    CreateWikiParams.model_validate({"slug": "home", "title": "Home", "created_by": "x"})

  with pytest.raises(ValidationError):
    CreateWikiParams.model_validate({"slug": "home", "title": "Home", "content": "body"})


def test_slug_and_route_context_models_require_fields():
  with pytest.raises(ValidationError):
    GetWikiBySlugParams.model_validate({})

  with pytest.raises(ValidationError):
    GetWikiByRouteContextParams.model_validate({})


def test_rpc_handlers_include_wiki_subdomains():
  assert "wiki" in PUBLIC_HANDLERS
  assert "wiki" in USERS_HANDLERS


def test_public_wiki_dispatchers_registered():
  module = importlib.import_module("rpc.public.wiki")
  dispatchers = module.DISPATCHERS
  assert ("get_page", "1") in dispatchers
  assert ("list_pages", "1") in dispatchers


def test_users_wiki_dispatchers_registered():
  module = importlib.import_module("rpc.users.wiki")
  dispatchers = module.DISPATCHERS
  assert ("create_version", "1") in dispatchers
  assert ("list_versions", "1") in dispatchers
  assert ("get_version", "1") in dispatchers


def test_content_wiki_module_has_expected_methods():
  module = importlib.import_module("server.modules.content_wiki_module")
  cls = module.ContentWikiModule

  for method in (
    "list_pages",
    "get_page",
    "get_page_by_slug",
    "get_page_by_route_context",
    "list_children",
    "create_page",
    "update_page",
    "delete_page",
    "create_version",
    "list_versions",
    "get_version",
  ):
    assert hasattr(cls, method)
