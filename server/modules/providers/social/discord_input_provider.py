"""Discord input provider that registers Discord bot commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TYPE_CHECKING

from discord.ext import commands

from . import SocialInputProvider

if TYPE_CHECKING:  # pragma: no cover
  from ...discord_bot_module import DiscordBotModule
  from ...social_input_module import SocialInputModule
  from discord.ext.commands import Bot


@dataclass(slots=True)
class DiscordCommandContext:
  guild_id: int | None
  channel_id: int | None
  user_id: int | None
  raw_context: Any


@dataclass(slots=True)
class RpcCommandRequest:
  context: DiscordCommandContext
  operation: str


@dataclass(slots=True)
class SummarizeCommandRequest:
  context: DiscordCommandContext
  hours_argument: str


@dataclass(slots=True)
class PersonaCommandRequest:
  context: DiscordCommandContext
  request_text: str | None


@dataclass(slots=True)
class DiscordCommandHandlers:
  rpc: Callable[[RpcCommandRequest], Awaitable[None]]
  summarize: Callable[[SummarizeCommandRequest], Awaitable[None]]
  persona: Callable[[PersonaCommandRequest], Awaitable[None]]


class DiscordInputProvider(SocialInputProvider):
  """Provider exposing Discord command wiring and DTO creation."""

  name = "discord"

  def __init__(self, module: "SocialInputModule", discord: "DiscordBotModule"):
    super().__init__(module)
    self.discord = discord
    self.bot: "Bot" | None = None
    self._registered: dict[str, commands.Command] = {}
    self._handlers: DiscordCommandHandlers | None = None

  def configure(self, handlers: DiscordCommandHandlers) -> None:
    self._handlers = handlers

  async def startup(self):
    if not self._handlers:
      raise RuntimeError("DiscordInputProvider handlers not configured")
    await self.discord.on_ready()
    if not self.discord.bot:
      raise RuntimeError("Discord bot is not initialized")
    self.bot = self.discord.bot
    self._register_commands()
    self.discord.register_input_provider(self)

  async def shutdown(self):
    if self.bot:
      for name in list(self._registered.keys()):
        self.bot.remove_command(name)
      self._registered.clear()
    self.bot = None

  def _register_commands(self) -> None:
    assert self.bot
    for name in list(self._registered.keys()):
      self.bot.remove_command(name)

    @commands.command(name="rpc")
    async def rpc_command(ctx, *, op: str):
      await self._dispatch_rpc(ctx, op)

    @commands.command(name="summarize")
    async def summarize_command(ctx, hours: str):
      await self._dispatch_summarize(ctx, hours)

    @commands.command(name="persona")
    async def persona_command(ctx, *, request: str | None = None):
      await self._dispatch_persona(ctx, request)

    self.bot.add_command(rpc_command)
    self.bot.add_command(summarize_command)
    self.bot.add_command(persona_command)
    self._registered = {
      "rpc": rpc_command,
      "summarize": summarize_command,
      "persona": persona_command,
    }

  async def _dispatch_rpc(self, ctx, op: str) -> None:
    assert self._handlers
    request = RpcCommandRequest(
      context=self._build_context(ctx),
      operation=op,
    )
    await self._handlers.rpc(request)

  async def _dispatch_summarize(self, ctx, hours: str) -> None:
    assert self._handlers
    request = SummarizeCommandRequest(
      context=self._build_context(ctx),
      hours_argument=hours,
    )
    await self._handlers.summarize(request)

  async def _dispatch_persona(self, ctx, request_text: str | None) -> None:
    assert self._handlers
    request = PersonaCommandRequest(
      context=self._build_context(ctx),
      request_text=request_text,
    )
    await self._handlers.persona(request)

  def _build_context(self, ctx) -> DiscordCommandContext:
    guild_id = getattr(getattr(ctx, "guild", None), "id", None)
    channel_id = getattr(getattr(ctx, "channel", None), "id", None)
    user_id = getattr(getattr(ctx, "author", None), "id", None)
    return DiscordCommandContext(
      guild_id=guild_id,
      channel_id=channel_id,
      user_id=user_id,
      raw_context=ctx,
    )

