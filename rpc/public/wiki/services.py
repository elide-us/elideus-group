from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request
from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import PublicWikiGetPage1, PublicWikiListPages1, PublicWikiPageItem1, PublicWikiPermissions1

if TYPE_CHECKING:
  from server.modules.content_wiki_module import ContentWikiModule


async def public_wiki_list_pages_v1(request: Request):
  rpc_request, auth_ctx, _user_ctx = await unbox_request(request)
  _ = auth_ctx
  payload = rpc_request.payload or {}
  parent_slug = payload.get("parent_slug")

  wiki_module: ContentWikiModule = request.app.state.content_wiki
  rows = await wiki_module.list_pages(parent_slug=parent_slug, is_active=True)

  pages = [
    PublicWikiPageItem1(
      slug=row["element_slug"],
      title=row["element_title"],
      parent_slug=row.get("element_parent_slug"),
      sequence=int(row.get("element_sequence") or 0),
      element_created_on=row.get("element_created_on"),
      element_modified_on=row.get("element_modified_on"),
    )
    for row in rows
  ]

  payload_model = PublicWikiListPages1(pages=pages)
  return RPCResponse(op=rpc_request.op, payload=payload_model.model_dump(), version=rpc_request.version)


async def public_wiki_get_page_v1(request: Request):
  rpc_request, auth_ctx, _user_ctx = await unbox_request(request)
  payload = rpc_request.payload or {}
  slug = payload.get("slug")
  if not slug:
    raise HTTPException(status_code=400, detail="Missing page slug")

  wiki_module: ContentWikiModule = request.app.state.content_wiki
  row = await wiki_module.get_page_by_slug(slug)
  if not row or not row.get("element_is_active"):
    raise HTTPException(status_code=404, detail="Page not found")

  children_rows = await wiki_module.list_children(slug)

  role_module = request.app.state.role
  access = role_module.check_content_access(
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
    owner_guid=row.get("element_created_by"),
  )

  permissions = PublicWikiPermissions1(
    can_edit=access.can_edit,
    can_delete=access.can_delete,
    is_owner=access.is_owner,
  )

  page = PublicWikiGetPage1(
    slug=row["element_slug"],
    title=row["element_title"],
    parent_slug=row.get("element_parent_slug"),
    route_context=row.get("element_route_context"),
    content=row.get("element_content"),
    version=row.get("element_version"),
    children=[
      PublicWikiPageItem1(
        slug=child["element_slug"],
        title=child["element_title"],
        parent_slug=child.get("element_parent_slug"),
        sequence=int(child.get("element_sequence") or 0),
        element_created_on=child.get("element_created_on"),
        element_modified_on=child.get("element_modified_on"),
      )
      for child in children_rows
    ],
    element_created_on=row.get("element_created_on"),
    element_modified_on=row.get("element_modified_on"),
    permissions=permissions,
  )

  return RPCResponse(op=rpc_request.op, payload=page.model_dump(), version=rpc_request.version)
