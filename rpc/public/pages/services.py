from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request
from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  PublicPagesGetPage1,
  PublicPagesListPages1,
  PublicPagesPageItem1,
  PublicPagesPermissions1,
)

if TYPE_CHECKING:
  from server.modules.content_pages_module import ContentPagesModule


async def public_pages_list_pages_v1(request: Request):
  rpc_request, auth_ctx, _user_ctx = await unbox_request(request)
  _ = auth_ctx
  payload = rpc_request.payload or {}
  page_type = payload.get("page_type")

  pages_module: ContentPagesModule = request.app.state.content_pages
  rows = await pages_module.list_pages(page_type=page_type, is_active=True)

  pages = [
    PublicPagesPageItem1(
      slug=row["element_slug"],
      title=row["element_title"],
      page_type=row["element_page_type"],
      category=row.get("element_category"),
      is_pinned=bool(row.get("element_is_pinned")),
      sequence=int(row.get("element_sequence") or 0),
      element_created_on=row.get("element_created_on"),
      element_modified_on=row.get("element_modified_on"),
    )
    for row in rows
  ]

  payload_model = PublicPagesListPages1(pages=pages)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload_model.model_dump(),
    version=rpc_request.version,
  )


async def public_pages_get_page_v1(request: Request):
  rpc_request, auth_ctx, _user_ctx = await unbox_request(request)
  payload = rpc_request.payload or {}
  slug = payload.get("slug")
  if not slug:
    raise HTTPException(status_code=400, detail="Missing page slug")

  pages_module: ContentPagesModule = request.app.state.content_pages
  row = await pages_module.get_page_by_slug(slug)
  if not row or not row.get("element_is_active"):
    raise HTTPException(status_code=404, detail="Page not found")

  role_module = request.app.state.role
  access = role_module.check_content_access(
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
    owner_guid=row.get("element_created_by"),
  )

  permissions = PublicPagesPermissions1(
    can_edit=access.can_edit,
    can_delete=access.can_delete,
    is_owner=access.is_owner,
  )

  page = PublicPagesGetPage1(
    slug=row["element_slug"],
    title=row["element_title"],
    page_type=row["element_page_type"],
    category=row.get("element_category"),
    content=row.get("element_content"),
    version=row.get("element_version"),
    element_created_on=row.get("element_created_on"),
    element_modified_on=row.get("element_modified_on"),
    permissions=permissions,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=page.model_dump(),
    version=rpc_request.version,
  )
