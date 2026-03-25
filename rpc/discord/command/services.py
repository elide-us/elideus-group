import logging

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.discord_bot_module import DiscordBotModule
from server.modules.finance_module import FinanceModule
from server.modules.oauth_module import OauthModule

from .models import (
  DiscordCommandGetCreditsRequest1,
  DiscordCommandGetCreditsResponse1,
  DiscordCommandGetGuildCreditsRequest1,
  DiscordCommandGetGuildCreditsResponse1,
  DiscordCommandGetRolesResponse1,
  DiscordCommandRegisterRequest1,
  DiscordCommandRegisterResponse1,
)


async def discord_command_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = DiscordCommandGetRolesResponse1(roles=auth_ctx.roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def discord_command_register_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = DiscordCommandRegisterRequest1.model_validate(rpc_request.payload or {})
  oauth: OauthModule = request.app.state.oauth
  await oauth.on_ready()
  result = await oauth.register_discord_user(payload.discord_id)
  response = DiscordCommandRegisterResponse1(**result)
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)


async def discord_command_get_credits_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  DiscordCommandGetCreditsRequest1.model_validate(rpc_request.payload or {})
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=403, detail="Registration required")

  finance: FinanceModule = request.app.state.finance
  await finance.on_ready()
  row = await finance.get_user_credits(auth_ctx.user_guid)
  response = DiscordCommandGetCreditsResponse1(
    credits=int(row.get("element_credits", 0) or 0),
    reserve=row.get("element_reserve"),
  )
  logging.info("[discord_command_get_credits_v1] fetched credits", extra={"user_guid": auth_ctx.user_guid})
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)


async def discord_command_get_guild_credits_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload = DiscordCommandGetGuildCreditsRequest1.model_validate(rpc_request.payload or {})

  discord_bot: DiscordBotModule = request.app.state.discord_bot
  await discord_bot.on_ready()
  credits = await discord_bot.get_guild_credits(payload.guild_id)
  response = DiscordCommandGetGuildCreditsResponse1(
    guild_id=payload.guild_id,
    credits=credits,
  )
  logging.info("[discord_command_get_guild_credits_v1] fetched guild credits", extra={"guild_id": payload.guild_id})
  return RPCResponse(op=rpc_request.op, payload=response.model_dump(), version=rpc_request.version)
