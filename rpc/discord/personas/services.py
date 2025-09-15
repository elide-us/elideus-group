import logging

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_personas_module import DiscordPersonasModule

from .models import (
  DiscordPersonasDeletePersona1,
  DiscordPersonasList1,
  DiscordPersonasModelItem1,
  DiscordPersonasModels1,
  DiscordPersonasPersonaItem1,
  DiscordPersonasUpsertPersona1,
)


async def discord_personas_get_personas_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[discord_personas_get_personas_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  module: DiscordPersonasModule = request.app.state.discord_personas
  rows = await module.list_personas()
  personas = [DiscordPersonasPersonaItem1(**row) for row in rows]
  payload = DiscordPersonasList1(personas=personas)
  logging.debug(
    "[discord_personas_get_personas_v1] returning %d personas",
    len(personas),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_personas_get_models_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[discord_personas_get_models_v1] user=%s roles=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
  )
  module: DiscordPersonasModule = request.app.state.discord_personas
  rows = await module.list_models()
  models = [DiscordPersonasModelItem1(**row) for row in rows]
  payload = DiscordPersonasModels1(models=models)
  logging.debug(
    "[discord_personas_get_models_v1] returning %d models",
    len(models),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_personas_upsert_persona_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[discord_personas_upsert_persona_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  payload = DiscordPersonasUpsertPersona1(**(rpc_request.payload or {}))
  module: DiscordPersonasModule = request.app.state.discord_personas
  await module.upsert_persona(payload.model_dump())
  logging.debug(
    "[discord_personas_upsert_persona_v1] upserted persona %s",
    payload.name,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_personas_delete_persona_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  logging.debug(
    "[discord_personas_delete_persona_v1] user=%s roles=%s payload=%s",
    auth_ctx.user_guid,
    auth_ctx.roles,
    rpc_request.payload,
  )
  payload = DiscordPersonasDeletePersona1(**(rpc_request.payload or {}))
  module: DiscordPersonasModule = request.app.state.discord_personas
  await module.delete_persona(recid=payload.recid, name=payload.name)
  logging.debug(
    "[discord_personas_delete_persona_v1] deleted persona recid=%s name=%s",
    payload.recid,
    payload.name,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
