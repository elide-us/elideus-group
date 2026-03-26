from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  ServicePagesCreatePage1,
  ServicePagesDeletePage1,
  ServicePagesListPages1,
  ServicePagesPageItem1,
  ServicePagesUpdatePage1,
)

if TYPE_CHECKING:
  from server.modules.content_pages_module import ContentPagesModule


def _to_page_item(row: dict) -> ServicePagesPageItem1:
  return ServicePagesPageItem1(
    recid=row["recid"],
    slug=row["element_slug"],
    title=row["element_title"],
    page_type=row["element_page_type"],
    category=row.get("element_category"),
    roles=row.get("element_roles", 0),
    is_active=row.get("element_is_active", True),
    is_pinned=row.get("element_is_pinned", False),
    sequence=row.get("element_sequence", 0),
    element_created_on=row.get("element_created_on"),
    element_modified_on=row.get("element_modified_on"),
  )


async def service_pages_list_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)

  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()

  pages = await module.list_pages()
  response = ServicePagesListPages1(pages=[_to_page_item(page) for page in pages])

  return RPCResponse(
    op=rpc_request.op,
    payload=response.model_dump(),
    version=rpc_request.version,
  )


async def service_pages_create_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = ServicePagesCreatePage1(**(rpc_request.payload or {}))

  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()

  page = await module.create_page(
    slug=payload.slug,
    title=payload.title,
    content=payload.content,
    created_by=auth_ctx.user_guid,
    page_type=payload.page_type,
    category=payload.category,
    roles=payload.roles,
    is_pinned=payload.is_pinned,
    sequence=payload.sequence,
    summary=payload.summary,
  )

  response = _to_page_item(page)
  return RPCResponse(
    op=rpc_request.op,
    payload=response.model_dump(),
    version=rpc_request.version,
  )


async def service_pages_update_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = ServicePagesUpdatePage1(**(rpc_request.payload or {}))

  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()

  page = await module.update_page(
    payload.recid,
    modified_by=auth_ctx.user_guid,
    title=payload.title,
    page_type=payload.page_type,
    category=payload.category,
    roles=payload.roles,
    is_active=payload.is_active,
    is_pinned=payload.is_pinned,
    sequence=payload.sequence,
  )

  response = _to_page_item(page)
  return RPCResponse(
    op=rpc_request.op,
    payload=response.model_dump(),
    version=rpc_request.version,
  )


async def service_pages_delete_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = ServicePagesDeletePage1(**(rpc_request.payload or {}))

  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()

  await module.delete_page(payload.recid, modified_by=auth_ctx.user_guid)

  return RPCResponse(
    op=rpc_request.op,
    payload={"success": True},
    version=rpc_request.version,
  )
