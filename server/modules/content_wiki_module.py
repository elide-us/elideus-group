from __future__ import annotations

from typing import Any

from fastapi import FastAPI

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

from . import BaseModule
from .db_module import DbModule


class ContentWikiModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.content_wiki = self
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def list_pages(self, parent_slug: str | None = None, is_active: bool | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_wiki_request(ListWikiParams(parent_slug=parent_slug, is_active=is_active)))
    return [dict(row) for row in res.rows]

  async def get_page(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_wiki_request(GetWikiParams(recid=recid)))
    return dict(res.rows[0]) if res.rows else None

  async def get_page_by_slug(self, slug: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_wiki_by_slug_request(GetWikiBySlugParams(slug=slug)))
    return dict(res.rows[0]) if res.rows else None

  async def get_page_by_route_context(self, route_context: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_wiki_by_route_context_request(GetWikiByRouteContextParams(route_context=route_context))
    )
    return dict(res.rows[0]) if res.rows else None

  async def list_children(self, parent_slug: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_children_request(ListChildrenParams(parent_slug=parent_slug)))
    return [dict(row) for row in res.rows]

  async def create_page(
    self,
    slug: str,
    title: str,
    content: str,
    created_by: str,
    *,
    parent_slug: str | None = None,
    route_context: str | None = None,
    roles: int = 0,
    sequence: int = 0,
    edit_summary: str | None = None,
  ) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      create_wiki_request(
        CreateWikiParams(
          slug=slug,
          title=title,
          content=content,
          created_by=created_by,
          parent_slug=parent_slug,
          route_context=route_context,
          roles=roles,
          sequence=sequence,
          edit_summary=edit_summary,
        )
      )
    )
    return dict(res.rows[0])

  async def update_page(
    self,
    recid: int,
    modified_by: str,
    *,
    title: str | None = None,
    parent_slug: str | None = None,
    route_context: str | None = None,
    roles: int | None = None,
    is_active: bool | None = None,
    sequence: int | None = None,
  ) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      update_wiki_request(
        UpdateWikiParams(
          recid=recid,
          modified_by=modified_by,
          title=title,
          parent_slug=parent_slug,
          route_context=route_context,
          roles=roles,
          is_active=is_active,
          sequence=sequence,
        )
      )
    )
    return dict(res.rows[0])

  async def delete_page(self, recid: int, modified_by: str) -> None:
    assert self.db
    await self.db.run(delete_wiki_request(DeleteWikiParams(recid=recid, modified_by=modified_by)))

  async def create_version(
    self,
    wiki_recid: int,
    content: str,
    created_by: str,
    *,
    edit_summary: str | None = None,
  ) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      create_version_request(
        CreateWikiVersionParams(
          wiki_recid=wiki_recid,
          content=content,
          created_by=created_by,
          edit_summary=edit_summary,
        )
      )
    )
    return dict(res.rows[0])

  async def list_versions(self, wiki_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_versions_request(ListWikiVersionsParams(wiki_recid=wiki_recid)))
    return [dict(row) for row in res.rows]

  async def get_version(
    self,
    *,
    recid: int | None = None,
    wiki_recid: int | None = None,
    version: int | None = None,
  ) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_version_request(GetWikiVersionParams(recid=recid, wiki_recid=wiki_recid, version=version))
    )
    return dict(res.rows[0]) if res.rows else None
