"""Coordinator module for social input providers."""

from __future__ import annotations

import asyncio, contextlib, json, logging, time
from typing import Any, Dict, TYPE_CHECKING

from fastapi import FastAPI

from . import BaseModule
from .providers.social.discord_input_provider import (
  DiscordCommandHandlers,
  DiscordInputProvider,
  PersonaCommandRequest,
  RpcCommandRequest,
  SummarizeCommandRequest,
)

if TYPE_CHECKING:  # pragma: no cover
  from .discord_bot_module import DiscordBotModule
  from .discord_chat_module import DiscordChatModule
  from .providers.social import SocialInputProvider


class SocialInputModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.providers: Dict[str, "SocialInputProvider"] = {}
    self.discord: "DiscordBotModule" | None = None
    self.discord_chat: "DiscordChatModule" | None = None
    self._provider_start_timeout = 15.0
    self._rpc_timeout = 30.0
    self._notice_timeout = 15.0
    self.app.state.social_input = self

  async def startup(self):
    self.discord = getattr(self.app.state, "discord_bot", None)
    self.discord_chat = getattr(self.app.state, "discord_chat", None)
    if self.discord_chat:
      await self.discord_chat.on_ready()
    if not self.discord:
      logging.info("[SocialInputModule] no Discord bot available; skipping provider registration")
      self.mark_ready()
      return
    await self.discord.on_ready()
    self.discord.register_social_input_module(self)
    provider = self._create_discord_provider(self.discord)
    provider.configure(self._build_handlers())
    task = asyncio.create_task(provider.startup())
    try:
      await asyncio.wait_for(task, timeout=self._provider_start_timeout)
    except Exception:
      await self._cancel_task(task)
      raise
    await self.register_provider(provider)
    logging.info("[SocialInputModule] loaded providers: %s", list(self.providers.keys()))
    self.mark_ready()

  async def shutdown(self):
    for name, provider in list(self.providers.items()):
      try:
        await provider.shutdown()
      finally:
        state_key = f"{name}_input_provider"
        if getattr(self.app.state, state_key, None) is provider:
          delattr(self.app.state, state_key)
        del self.providers[name]
    if getattr(self.app.state, "social_input", None) is self:
      self.app.state.social_input = None
    self.discord = None
    self.discord_chat = None

  async def register_provider(self, provider: "SocialInputProvider"):
    name = provider.name
    if name in self.providers:
      raise ValueError(f"Provider '{name}' already registered")
    self.providers[name] = provider
    setattr(self.app.state, f"{name}_input_provider", provider)

  async def dispatch(self, provider_name: str, action: str, *args, **kwargs) -> Any:
    provider = self.providers.get(provider_name)
    if not provider:
      raise ValueError(f"Provider '{provider_name}' not registered")
    return await provider.dispatch(action, *args, **kwargs)

  def get_provider(self, name: str) -> "SocialInputProvider | None":
    return self.providers.get(name)

  def _create_discord_provider(self, discord: "DiscordBotModule") -> DiscordInputProvider:
    return DiscordInputProvider(self, discord)

  def _build_handlers(self) -> DiscordCommandHandlers:
    return DiscordCommandHandlers(
      rpc=self.handle_rpc_command,
      summarize=self.handle_summarize_command,
      persona=self.handle_persona_command,
    )

  async def handle_rpc_command(self, request: RpcCommandRequest) -> None:
    context = request.context
    discord = self._require_discord()
    guild_id = context.guild_id or 0
    user_id = context.user_id or 0
    channel_id = context.channel_id or 0
    if guild_id and user_id:
      discord.bump_rate_limits(guild_id, user_id)
    metadata = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "user_id": user_id,
    }
    start = time.perf_counter()
    rpc_task = asyncio.create_task(discord.call_rpc(request.operation, None, metadata=metadata))
    try:
      response = await asyncio.wait_for(rpc_task, timeout=self._rpc_timeout)
    except asyncio.TimeoutError:
      await self._cancel_task(rpc_task)
      await self._queue_channel_notice(context, "Request timed out.", reason="rpc_timeout")
      logging.exception(
        "[SocialInputModule] rpc timed out",
        extra={"op": request.operation, "guild_id": guild_id, "channel_id": channel_id, "user_id": user_id},
      )
      return
    except Exception as exc:
      await self._cancel_task(rpc_task)
      await self._queue_channel_notice(context, f"Error: {exc}", reason="rpc_command_error")
      elapsed = time.perf_counter() - start
      logging.exception(
        "[SocialInputModule] rpc failed",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "op": request.operation,
          "elapsed": elapsed,
        },
      )
      return
    payload = response.payload
    message = self._format_payload(payload)
    await self._queue_channel_notice(context, message, reason="rpc_command")
    elapsed = time.perf_counter() - start
    logging.info(
      "[SocialInputModule] rpc",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "op": request.operation,
        "elapsed": elapsed,
      },
    )

  async def handle_summarize_command(self, request: SummarizeCommandRequest) -> None:
    context = request.context
    discord = self._require_discord()
    guild_id = context.guild_id or 0
    user_id = context.user_id or 0
    channel_id = context.channel_id or 0
    if guild_id and user_id:
      discord.bump_rate_limits(guild_id, user_id)
    try:
      hours = int(request.hours_argument)
    except (TypeError, ValueError):
      await self._queue_channel_notice(context, "Usage: !summarize <hours>", reason="invalid_hours")
      return
    if hours < 1 or hours > 336:
      await self._queue_channel_notice(context, "Hours must be between 1 and 336", reason="hours_out_of_range")
      return
    payload = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "hours": hours,
      "user_id": user_id,
    }
    metadata = {
      "guild_id": guild_id,
      "channel_id": channel_id,
      "user_id": user_id,
    }
    start = time.perf_counter()
    rpc_task = asyncio.create_task(
      discord.call_rpc("urn:discord:chat:summarize_channel:1", payload, metadata=metadata)
    )
    try:
      response = await asyncio.wait_for(rpc_task, timeout=self._rpc_timeout)
    except asyncio.TimeoutError:
      await self._cancel_task(rpc_task)
      await self._queue_channel_notice(
        context,
        "Failed to fetch messages. Please try again later.",
        reason="rpc_timeout",
      )
      logging.exception(
        "[SocialInputModule] summarize timed out",
        extra={"guild_id": guild_id, "channel_id": channel_id, "user_id": user_id, "hours": hours},
      )
      return
    except Exception:
      await self._cancel_task(rpc_task)
      await self._queue_channel_notice(
        context,
        "Failed to fetch messages. Please try again later.",
        reason="rpc_failure",
      )
      elapsed = time.perf_counter() - start
      logging.exception(
        "[SocialInputModule] summarize failed",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "hours": hours,
          "elapsed": elapsed,
        },
      )
      return
    result = self._coerce_payload_dict(response.payload)
    if not result.get("success"):
      message = result.get("ack_message") or "Failed to send summary. Please try again later."
      await self._queue_channel_notice(
        context,
        message,
        reason=result.get("reason") or "delivery_failed",
        details=result,
      )
    elapsed = time.perf_counter() - start
    logging.info(
      "[SocialInputModule] summarize",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "hours": hours,
        "token_count_estimate": result.get("token_count_estimate"),
        "messages_collected": result.get("messages_collected"),
        "cap_hit": result.get("cap_hit"),
        "queue_id": result.get("queue_id"),
        "dm_enqueued": result.get("dm_enqueued"),
        "channel_ack_enqueued": result.get("channel_ack_enqueued"),
        "reason": result.get("reason"),
        "elapsed": elapsed,
      },
    )

  async def handle_persona_command(self, request: PersonaCommandRequest) -> None:
    context = request.context
    discord = self._require_discord()
    guild_id = context.guild_id or 0
    user_id = context.user_id or 0
    channel_id = context.channel_id or 0
    if guild_id and user_id:
      discord.bump_rate_limits(guild_id, user_id)
    command_text = (request.request_text or "").strip()
    if not command_text:
      await self._queue_channel_notice(context, "Usage: !persona <persona> <message>", reason="invalid_persona_usage")
      return
    chat_module = self.discord_chat
    if not chat_module:
      await self._queue_channel_notice(
        context,
        "Persona chat is currently unavailable.",
        reason="persona_module_unavailable",
      )
      return
    try:
      task = asyncio.create_task(
        chat_module.handle_persona_command(
          guild_id=guild_id,
          channel_id=channel_id,
          user_id=user_id,
          command_text=command_text,
        )
      )
      result = await asyncio.wait_for(task, timeout=self._rpc_timeout)
    except ValueError:
      await self._cancel_task(task)
      await self._queue_channel_notice(context, "Usage: !persona <persona> <message>", reason="invalid_persona_usage")
      return
    except asyncio.TimeoutError:
      await self._cancel_task(task)
      await self._queue_channel_notice(
        context,
        "Persona chat is currently unavailable.",
        reason="persona_timeout",
      )
      logging.exception(
        "[SocialInputModule] persona timed out",
        extra={"guild_id": guild_id, "channel_id": channel_id, "user_id": user_id},
      )
      return
    except Exception:
      await self._cancel_task(task)
      await self._queue_channel_notice(
        context,
        "Persona chat is currently unavailable.",
        reason="persona_rpc_failure",
      )
      logging.exception(
        "[SocialInputModule] persona failed",
        extra={
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "request": command_text,
        },
      )
      return
    ack_message = result.get("ack_message")
    reason = result.get("reason") or ("persona_response" if result.get("success") else "persona_failed")
    logging.info(
      "[SocialInputModule] persona",
      extra={
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "persona": result.get("persona"),
        "success": result.get("success"),
        "reason": reason,
      },
    )
    if ack_message:
      await self._send_channel_message(context, ack_message, reason=reason)

  def _require_discord(self) -> "DiscordBotModule":
    if not self.discord:
      raise RuntimeError("Discord bot module is not available")
    return self.discord

  async def _queue_channel_notice(
    self,
    context,
    message: str,
    *,
    reason: str | None = None,
    success: bool = False,
    details: Dict[str, Any] | None = None,
  ) -> None:
    if not message:
      return
    details = details or {}
    guild_id = context.guild_id or 0
    channel_id = context.channel_id
    user_id = context.user_id
    if self.discord_chat:
      try:
        task = asyncio.create_task(
          self.discord_chat.deliver_summary(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            summary_text=details.get("summary_text"),
            ack_message=message,
            success=success,
            reason=reason,
            messages_collected=details.get("messages_collected"),
            token_count_estimate=details.get("token_count_estimate"),
            cap_hit=details.get("cap_hit"),
          )
        )
        await asyncio.wait_for(task, timeout=self._notice_timeout)
        return
      except Exception:
        await self._cancel_task(task)
        logging.exception(
          "[SocialInputModule] failed to queue channel notice",
          extra={
            "channel_id": channel_id,
            "guild_id": guild_id,
            "user_id": user_id,
            "reason": reason,
          },
        )
    await self._send_channel_message(context, message, reason=reason)

  async def _send_channel_message(self, context, message: str, *, reason: str | None = None) -> None:
    if not message:
      return
    discord = self.discord
    channel_id = context.channel_id
    if not discord or not channel_id:
      return
    task = asyncio.create_task(discord.send_channel_message(channel_id, message))
    try:
      await asyncio.wait_for(task, timeout=self._notice_timeout)
    except Exception:
      await self._cancel_task(task)
      logging.exception(
        "[SocialInputModule] failed to send channel message",
        extra={"channel_id": channel_id, "reason": reason},
      )

  async def _cancel_task(self, task: asyncio.Task[Any]) -> None:
    if task.done():
      return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
      await task

  def _format_payload(self, payload: Any) -> str:
    if payload is None:
      return "Success"
    if hasattr(payload, "model_dump"):
      try:
        return json.dumps(payload.model_dump())
      except Exception:
        return str(payload)
    if isinstance(payload, dict):
      try:
        return json.dumps(payload)
      except Exception:
        return str(payload)
    return str(payload)

  def _coerce_payload_dict(self, payload: Any) -> Dict[str, Any]:
    if payload is None:
      return {}
    if hasattr(payload, "model_dump"):
      try:
        return dict(payload.model_dump())
      except Exception:
        return {"payload": str(payload)}
    if isinstance(payload, dict):
      return dict(payload)
    return {"success": bool(payload)}

