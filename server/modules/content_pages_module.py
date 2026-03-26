from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule
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


class ContentPagesModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.content_pages = self
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def list_pages(self, page_type: str | None = None, is_active: bool | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_pages_request(ListPagesParams(page_type=page_type, is_active=is_active)))
    return [dict(row) for row in res.rows]

  async def get_page(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_page_request(GetPageParams(recid=recid)))
    return dict(res.rows[0]) if res.rows else None

  async def get_page_by_slug(self, slug: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_page_by_slug_request(GetPageBySlugParams(slug=slug)))
    return dict(res.rows[0]) if res.rows else None

  async def create_page(
    self,
    slug: str,
    title: str,
    content: str,
    created_by: str,
    *,
    page_type: str = "article",
    category: str | None = None,
    roles: int = 0,
    is_pinned: bool = False,
    sequence: int = 0,
    summary: str | None = None,
  ) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      create_page_request(
        CreatePageParams(
          slug=slug,
          title=title,
          content=content,
          created_by=created_by,
          page_type=page_type,
          category=category,
          roles=roles,
          is_pinned=is_pinned,
          sequence=sequence,
          summary=summary,
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
    page_type: str | None = None,
    category: str | None = None,
    roles: int | None = None,
    is_active: bool | None = None,
    is_pinned: bool | None = None,
    sequence: int | None = None,
  ) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      update_page_request(
        UpdatePageParams(
          recid=recid,
          modified_by=modified_by,
          title=title,
          page_type=page_type,
          category=category,
          roles=roles,
          is_active=is_active,
          is_pinned=is_pinned,
          sequence=sequence,
        )
      )
    )
    return dict(res.rows[0])

  async def delete_page(self, recid: int, modified_by: str) -> None:
    assert self.db
    await self.db.run(delete_page_request(DeletePageParams(recid=recid, modified_by=modified_by)))

  async def create_version(
    self,
    pages_recid: int,
    content: str,
    created_by: str,
    *,
    summary: str | None = None,
  ) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      create_version_request(
        CreateVersionParams(
          pages_recid=pages_recid,
          content=content,
          created_by=created_by,
          summary=summary,
        )
      )
    )
    return dict(res.rows[0])

  async def list_versions(self, pages_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_versions_request(ListVersionsParams(pages_recid=pages_recid)))
    return [dict(row) for row in res.rows]

  async def get_version(
    self,
    *,
    recid: int | None = None,
    pages_recid: int | None = None,
    version: int | None = None,
  ) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_version_request(GetVersionParams(recid=recid, pages_recid=pages_recid, version=version))
    )
    return dict(res.rows[0]) if res.rows else None
