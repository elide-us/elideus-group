from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  UsersWikiCreatePage1,
  UsersWikiCreateVersion1,
  UsersWikiGetVersion1,
  UsersWikiListVersions1,
  UsersWikiVersionContent1,
  UsersWikiVersionList1,
)

if TYPE_CHECKING:
  from server.modules.content_wiki_module import ContentWikiModule


async def users_wiki_create_version_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersWikiCreateVersion1(**(rpc_request.payload or {}))
  module: ContentWikiModule = request.app.state.content_wiki
  await module.on_ready()
  result: UsersWikiVersionContent1 = await module.create_version(
    slug=payload.slug,
    content=payload.content,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
    edit_summary=payload.edit_summary,
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def users_wiki_create_page_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersWikiCreatePage1(**(rpc_request.payload or {}))
  module: ContentWikiModule = request.app.state.content_wiki
  await module.on_ready()
  result: UsersWikiVersionContent1 = await module.create_page(
    slug=payload.slug,
    title=payload.title,
    content=payload.content,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
    parent_slug=payload.parent_slug,
    edit_summary=payload.edit_summary,
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def users_wiki_list_versions_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersWikiListVersions1(**(rpc_request.payload or {}))
  module: ContentWikiModule = request.app.state.content_wiki
  await module.on_ready()
  result: UsersWikiVersionList1 = await module.list_versions(
    slug=payload.slug,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)


async def users_wiki_get_version_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersWikiGetVersion1(**(rpc_request.payload or {}))
  module: ContentWikiModule = request.app.state.content_wiki
  await module.on_ready()
  result: UsersWikiVersionContent1 = await module.get_version(
    slug=payload.slug,
    version=payload.version,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
  )

  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)
