from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  UsersPagesCreateVersion1,
  UsersPagesGetVersion1,
  UsersPagesListVersions1,
  UsersPagesVersionContent1,
  UsersPagesVersionList1,
)

if TYPE_CHECKING:
  from server.modules.content_pages_module import ContentPagesModule


async def users_pages_create_version_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersPagesCreateVersion1(**(rpc_request.payload or {}))
  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()
  result: UsersPagesVersionContent1 = await module.create_version(
    slug=payload.slug,
    content=payload.content,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
    summary=payload.summary,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def users_pages_list_versions_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersPagesListVersions1(**(rpc_request.payload or {}))
  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()
  result: UsersPagesVersionList1 = await module.list_versions(
    slug=payload.slug,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def users_pages_get_version_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = UsersPagesGetVersion1(**(rpc_request.payload or {}))
  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()
  result: UsersPagesVersionContent1 = await module.get_version(
    slug=payload.slug,
    version=payload.version,
    user_guid=auth_ctx.user_guid,
    role_mask=auth_ctx.role_mask,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )
