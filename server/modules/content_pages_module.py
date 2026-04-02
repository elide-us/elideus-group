from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from fastapi import FastAPI, HTTPException

from . import BaseModule
from .db_module import DbModule
from server.models import ContentAccess
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

if TYPE_CHECKING:
  from rpc.users.pages.models import UsersPagesVersionContent1, UsersPagesVersionList1, UsersPagesVersionItem1
  from .role_module import RoleModule


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
    slug: str,
    content: str,
    user_guid: str | None,
    role_mask: int,
    *,
    summary: str | None = None,
  ) -> UsersPagesVersionContent1:
    page, access = await self._resolve_editable_page(slug=slug, user_guid=user_guid, role_mask=role_mask)
    assert self.db
    res = await self.db.run(
      create_version_request(
        CreateVersionParams(
          pages_recid=page["recid"],
          content=content,
          created_by=user_guid,
          summary=summary,
        )
      )
    )
    version = dict(res.rows[0])
    from rpc.users.pages.models import UsersPagesVersionContent1

    return UsersPagesVersionContent1(
      recid=version["recid"],
      element_version=version["element_version"],
      element_content=version["element_content"],
      element_summary=version.get("element_summary"),
      element_created_by=version["element_created_by"],
      element_created_on=version.get("element_created_on"),
      access=access,
    )

  async def list_versions(
    self,
    slug: str,
    user_guid: str | None,
    role_mask: int,
  ) -> UsersPagesVersionList1:
    page, access = await self._resolve_editable_page(slug=slug, user_guid=user_guid, role_mask=role_mask)
    assert self.db
    res = await self.db.run(list_versions_request(ListVersionsParams(pages_recid=page["recid"])))
    versions = [dict(row) for row in res.rows]
    from rpc.users.pages.models import UsersPagesVersionItem1, UsersPagesVersionList1

    return UsersPagesVersionList1(
      versions=[
        UsersPagesVersionItem1(
          recid=version["recid"],
          element_version=version["element_version"],
          element_summary=version.get("element_summary"),
          element_created_by=version["element_created_by"],
          element_created_on=version.get("element_created_on"),
        )
        for version in versions
      ],
      access=access,
    )

  async def get_version(
    self,
    slug: str,
    version: int,
    user_guid: str | None,
    role_mask: int,
  ) -> UsersPagesVersionContent1:
    page, access = await self._resolve_editable_page(slug=slug, user_guid=user_guid, role_mask=role_mask)
    assert self.db
    res = await self.db.run(
      get_version_request(GetVersionParams(recid=None, pages_recid=page["recid"], version=version))
    )
    if not res.rows:
      raise HTTPException(status_code=404, detail="Version not found")
    version_row = dict(res.rows[0])
    from rpc.users.pages.models import UsersPagesVersionContent1

    return UsersPagesVersionContent1(
      recid=version_row["recid"],
      element_version=version_row["element_version"],
      element_content=version_row["element_content"],
      element_summary=version_row.get("element_summary"),
      element_created_by=version_row["element_created_by"],
      element_created_on=version_row.get("element_created_on"),
      access=access,
    )

  async def review_content(self, payload: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Content review is not yet implemented")

  async def _resolve_editable_page(
    self,
    *,
    slug: str,
    user_guid: str | None,
    role_mask: int,
  ) -> tuple[dict[str, Any], ContentAccess]:
    if user_guid is None:
      raise HTTPException(status_code=401, detail="Authentication required")

    page = await self.get_page_by_slug(slug)
    if not page:
      raise HTTPException(status_code=404, detail="Page not found")

    role_module: RoleModule = self.app.state.role
    access = role_module.check_content_access(
      user_guid=user_guid,
      role_mask=role_mask,
      owner_guid=page.get("element_created_by"),
    )
    if not access.can_edit:
      raise HTTPException(status_code=403, detail="Forbidden")
    return page, access
