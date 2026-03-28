from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  UsersWikiCreatePage1,
  UsersWikiCreateVersion1,
  UsersWikiGetVersion1,
  UsersWikiListVersions1,
  UsersWikiVersionContent1,
  UsersWikiVersionItem1,
  UsersWikiVersionList1,
)

if TYPE_CHECKING:
  from server.modules.content_wiki_module import ContentWikiModule


def _ensure_authenticated(user_guid: str | None):
  if not user_guid:
    raise HTTPException(status_code=401, detail="Authentication required")


async def _resolve_editable_page(request: Request, slug: str, user_guid: str, role_mask: int):
  module: ContentWikiModule = request.app.state.content_wiki
  page = await module.get_page_by_slug(slug)
  if not page:
    raise HTTPException(status_code=404, detail="Page not found")

  role_module = request.app.state.role
  access = role_module.check_content_access(
    user_guid=user_guid,
    role_mask=role_mask,
    owner_guid=page.get("element_created_by"),
  )
  if not access.can_edit:
    raise HTTPException(status_code=403, detail="Forbidden")

  return page


async def users_wiki_create_version_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  _ensure_authenticated(auth_ctx.user_guid)

  payload = UsersWikiCreateVersion1(**(rpc_request.payload or {}))
  page = await _resolve_editable_page(request, payload.slug, auth_ctx.user_guid, auth_ctx.role_mask)

  module: ContentWikiModule = request.app.state.content_wiki
  version = await module.create_version(
    wiki_recid=page["recid"],
    content=payload.content,
    created_by=auth_ctx.user_guid,
    edit_summary=payload.edit_summary,
  )

  result = UsersWikiVersionContent1(
    recid=version["recid"],
    element_version=version["element_version"],
    element_content=version["element_content"],
    element_edit_summary=version.get("element_edit_summary"),
    element_created_by=version["element_created_by"],
    element_created_on=version.get("element_created_on"),
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def users_wiki_create_page_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  _ensure_authenticated(auth_ctx.user_guid)

  payload = UsersWikiCreatePage1(**(rpc_request.payload or {}))

  module: ContentWikiModule = request.app.state.content_wiki
  existing = await module.get_page_by_slug(payload.slug)
  if existing:
    raise HTTPException(status_code=409, detail="Page already exists")

  page = await module.create_page(
    slug=payload.slug,
    title=payload.title,
    content=payload.content,
    created_by=auth_ctx.user_guid,
    parent_slug=payload.parent_slug,
    edit_summary=payload.edit_summary,
  )

  result = UsersWikiVersionContent1(
    recid=page.get("recid", 0),
    element_version=page.get("element_version", 1),
    element_content=page.get("element_content", ""),
    element_edit_summary=page.get("element_edit_summary"),
    element_created_by=page.get("element_created_by", ""),
    element_created_on=page.get("element_created_on"),
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def users_wiki_list_versions_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  _ensure_authenticated(auth_ctx.user_guid)

  payload = UsersWikiListVersions1(**(rpc_request.payload or {}))
  page = await _resolve_editable_page(request, payload.slug, auth_ctx.user_guid, auth_ctx.role_mask)

  module: ContentWikiModule = request.app.state.content_wiki
  versions = await module.list_versions(page["recid"])

  result = UsersWikiVersionList1(
    versions=[
      UsersWikiVersionItem1(
        recid=version["recid"],
        element_version=version["element_version"],
        element_edit_summary=version.get("element_edit_summary"),
        element_created_by=version["element_created_by"],
        element_created_on=version.get("element_created_on"),
      )
      for version in versions
    ]
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def users_wiki_get_version_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  _ensure_authenticated(auth_ctx.user_guid)

  payload = UsersWikiGetVersion1(**(rpc_request.payload or {}))
  page = await _resolve_editable_page(request, payload.slug, auth_ctx.user_guid, auth_ctx.role_mask)

  module: ContentWikiModule = request.app.state.content_wiki
  version = await module.get_version(wiki_recid=page["recid"], version=payload.version)
  if not version:
    raise HTTPException(status_code=404, detail="Version not found")

  result = UsersWikiVersionContent1(
    recid=version["recid"],
    element_version=version["element_version"],
    element_content=version["element_content"],
    element_edit_summary=version.get("element_edit_summary"),
    element_created_by=version["element_created_by"],
    element_created_on=version.get("element_created_on"),
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)
