from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.oauth_module import OauthModule
from .models import (
  UsersProvidersSetProvider1,
  UsersProvidersLinkProvider1,
  UsersProvidersUnlinkProvider1,
  UsersProvidersGetByProviderIdentifier1,
  UsersProvidersCreateFromProvider1,
)

async def users_providers_set_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersSetProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  provider = payload.provider.lower()
  module: OauthModule = request.app.state.oauth
  await module.on_ready()
  result = await module.set_user_default_provider(
    auth_ctx.user_guid,
    provider,
    code=payload.code,
    id_token=payload.id_token,
    access_token=payload.access_token,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )

async def users_providers_link_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersLinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  provider = payload.provider.lower()
  module: OauthModule = request.app.state.oauth
  await module.on_ready()
  result = await module.link_user_provider(
    auth_ctx.user_guid,
    provider,
    code=payload.code,
    id_token=payload.id_token,
    access_token=payload.access_token,
  )
  return RPCResponse(op=rpc_request.op, payload=result, version=rpc_request.version)

async def users_providers_unlink_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersUnlinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  provider = payload.provider.lower()
  module: OauthModule = request.app.state.oauth
  await module.on_ready()
  result = await module.unlink_user_provider(
    auth_ctx.user_guid,
    provider,
    new_default=payload.new_default,
  )
  return RPCResponse(op=rpc_request.op, payload=result, version=rpc_request.version)

async def users_providers_get_by_provider_identifier_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersGetByProviderIdentifier1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  provider = payload.provider.lower()
  module: OauthModule = request.app.state.oauth
  await module.on_ready()
  row = await module.get_user_by_provider_identifier(
    provider, payload.provider_identifier
  )
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

async def users_providers_create_from_provider_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersCreateFromProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  provider = payload.provider.lower()
  module: OauthModule = request.app.state.oauth
  await module.on_ready()
  row = await module.create_user_from_provider(
    provider,
    payload.provider_identifier,
    payload.provider_email,
    payload.provider_displayname,
    payload.provider_profile_image,
  )
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)
