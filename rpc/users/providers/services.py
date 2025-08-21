from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
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
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": auth_ctx.user_guid,
    "provider": payload.provider,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_providers_link_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersLinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db
  provider_uid, _, _ = await auth.handle_auth_login(payload.provider, payload.id_token, payload.access_token)
  res = await db.run(
    "urn:users:providers:get_by_provider_identifier:1",
    {"provider": payload.provider, "provider_identifier": provider_uid},
  )
  if res.rows and res.rows[0].get("guid") != auth_ctx.user_guid:
    raise HTTPException(status_code=409, detail="Provider already linked")
  await db.run(
    "urn:users:providers:link_provider:1",
    {
      "guid": auth_ctx.user_guid,
      "provider": payload.provider,
      "provider_identifier": provider_uid,
    },
  )
  return RPCResponse(op=rpc_request.op, payload={"provider": payload.provider}, version=rpc_request.version)

async def users_providers_unlink_provider_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  try:
    payload = UsersProvidersUnlinkProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  await db.run(
    "urn:users:providers:unlink_provider:1",
    {"guid": auth_ctx.user_guid, "provider": payload.provider},
  )
  return RPCResponse(op=rpc_request.op, payload={"provider": payload.provider}, version=rpc_request.version)

async def users_providers_get_by_provider_identifier_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersGetByProviderIdentifier1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  res = await db.run(
    "urn:users:providers:get_by_provider_identifier:1",
    payload.model_dump(),
  )
  row = res.rows[0] if res.rows else None
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

async def users_providers_create_from_provider_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    payload = UsersProvidersCreateFromProvider1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
  db: DbModule = request.app.state.db
  res = await db.run(
    "urn:users:providers:get_user_by_email:1",
    {"email": payload.provider_email},
  )
  if res.rows:
    raise HTTPException(status_code=409, detail="Email already registered")
  res = await db.run(
    "urn:users:providers:create_from_provider:1",
    payload.model_dump(),
  )
  row = res.rows[0] if res.rows else None
  return RPCResponse(op=rpc_request.op, payload=row, version=rpc_request.version)

