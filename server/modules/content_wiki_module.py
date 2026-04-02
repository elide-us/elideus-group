from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from fastapi import FastAPI, HTTPException

from server.models import ContentAccess
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

if TYPE_CHECKING:
  from rpc.users.wiki.models import UsersWikiVersionContent1, UsersWikiVersionList1, UsersWikiVersionItem1
  from .role_module import RoleModule


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
    user_guid: str | None,
    role_mask: int,
    *,
    parent_slug: str | None = None,
    route_context: str | None = None,
    roles: int = 0,
    sequence: int = 0,
    edit_summary: str | None = None,
  ) -> UsersWikiVersionContent1:
    self._ensure_authenticated(user_guid)
    access = await self._ensure_wiki_creation_allowed(user_guid=user_guid, role_mask=role_mask)
    assert self.db
    existing = await self.get_page_by_slug(slug)
    if existing:
      raise HTTPException(status_code=409, detail="Page already exists")

    res = await self.db.run(
      create_wiki_request(
        CreateWikiParams(
          slug=slug,
          title=title,
          content=content,
          created_by=user_guid,
          parent_slug=parent_slug,
          route_context=route_context,
          roles=roles,
          sequence=sequence,
          edit_summary=edit_summary,
        )
      )
    )
    page = dict(res.rows[0])
    from rpc.users.wiki.models import UsersWikiVersionContent1

    return UsersWikiVersionContent1(
      recid=page.get("recid", 0),
      element_version=page.get("element_version", 1),
      element_content=page.get("element_content", ""),
      element_edit_summary=page.get("element_edit_summary"),
      element_created_by=page.get("element_created_by", ""),
      element_created_on=page.get("element_created_on"),
      access=access,
    )

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
    slug: str,
    content: str,
    user_guid: str | None,
    role_mask: int,
    *,
    edit_summary: str | None = None,
  ) -> UsersWikiVersionContent1:
    page, access = await self._resolve_editable_page(slug=slug, user_guid=user_guid, role_mask=role_mask)
    assert self.db
    res = await self.db.run(
      create_version_request(
        CreateWikiVersionParams(
          wiki_recid=page["recid"],
          content=content,
          created_by=user_guid,
          edit_summary=edit_summary,
        )
      )
    )
    version = dict(res.rows[0])
    from rpc.users.wiki.models import UsersWikiVersionContent1

    return UsersWikiVersionContent1(
      recid=version["recid"],
      element_version=version["element_version"],
      element_content=version["element_content"],
      element_edit_summary=version.get("element_edit_summary"),
      element_created_by=version["element_created_by"],
      element_created_on=version.get("element_created_on"),
      access=access,
    )

  async def list_versions(
    self,
    slug: str,
    user_guid: str | None,
    role_mask: int,
  ) -> UsersWikiVersionList1:
    page, access = await self._resolve_editable_page(slug=slug, user_guid=user_guid, role_mask=role_mask)
    assert self.db
    res = await self.db.run(list_versions_request(ListWikiVersionsParams(wiki_recid=page["recid"])))
    versions = [dict(row) for row in res.rows]
    from rpc.users.wiki.models import UsersWikiVersionItem1, UsersWikiVersionList1

    return UsersWikiVersionList1(
      versions=[
        UsersWikiVersionItem1(
          recid=version["recid"],
          element_version=version["element_version"],
          element_edit_summary=version.get("element_edit_summary"),
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
  ) -> UsersWikiVersionContent1:
    page, access = await self._resolve_editable_page(slug=slug, user_guid=user_guid, role_mask=role_mask)
    assert self.db
    res = await self.db.run(
      get_version_request(GetWikiVersionParams(recid=None, wiki_recid=page["recid"], version=version))
    )
    if not res.rows:
      raise HTTPException(status_code=404, detail="Version not found")
    version_row = dict(res.rows[0])
    from rpc.users.wiki.models import UsersWikiVersionContent1

    return UsersWikiVersionContent1(
      recid=version_row["recid"],
      element_version=version_row["element_version"],
      element_content=version_row["element_content"],
      element_edit_summary=version_row.get("element_edit_summary"),
      element_created_by=version_row["element_created_by"],
      element_created_on=version_row.get("element_created_on"),
      access=access,
    )

  def _ensure_authenticated(self, user_guid: str | None):
    if user_guid is None:
      raise HTTPException(status_code=401, detail="Authentication required")

  async def _ensure_wiki_creation_allowed(
    self,
    *,
    user_guid: str | None,
    role_mask: int,
  ) -> ContentAccess:
    self._ensure_authenticated(user_guid)
    role_module: RoleModule = self.app.state.role
    access = role_module.check_content_access(
      user_guid=user_guid,
      role_mask=role_mask,
      owner_guid=user_guid,
    )
    if not access.can_edit:
      raise HTTPException(status_code=403, detail="Forbidden")
    return access

  async def _resolve_editable_page(
    self,
    *,
    slug: str,
    user_guid: str | None,
    role_mask: int,
  ) -> tuple[dict[str, Any], ContentAccess]:
    self._ensure_authenticated(user_guid)
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
