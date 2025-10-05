import asyncio
from types import SimpleNamespace

import discord
from discord.ext import commands

from server.modules.providers.social.discord_input_provider import (
  DiscordCommandHandlers,
  DiscordInputProvider,
  PersonaCommandRequest,
  RpcCommandRequest,
  SummarizeCommandRequest,
)


class DummyDiscord:
  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    self.bot = commands.Bot(command_prefix="!", intents=intents)
    self.app = SimpleNamespace()
    self.registered = None

  async def on_ready(self):  # pragma: no cover - matches production signature
    return

  def register_input_provider(self, provider):
    self.registered = provider


def test_provider_dispatches_command_dtos():
  discord = DummyDiscord()
  provider = DiscordInputProvider(SimpleNamespace(), discord)
  events: dict[str, object] = {}

  async def rpc_handler(request: RpcCommandRequest):
    events["rpc"] = request

  async def summarize_handler(request: SummarizeCommandRequest):
    events["summarize"] = request

  async def persona_handler(request: PersonaCommandRequest):
    events["persona"] = request

  async def run_test():
    provider.configure(
      DiscordCommandHandlers(
        rpc=rpc_handler,
        summarize=summarize_handler,
        persona=persona_handler,
      )
    )

    await provider.startup()

    ctx = SimpleNamespace(
      guild=SimpleNamespace(id=42),
      channel=SimpleNamespace(id=11),
      author=SimpleNamespace(id=7),
    )

    rpc_cmd = discord.bot.get_command("rpc")
    summarize_cmd = discord.bot.get_command("summarize")
    persona_cmd = discord.bot.get_command("persona")

    await rpc_cmd.callback(ctx, op="urn:test:1")
    await summarize_cmd.callback(ctx, hours="24")
    await persona_cmd.callback(ctx, request="helper hi")

    assert isinstance(events["rpc"], RpcCommandRequest)
    assert events["rpc"].operation == "urn:test:1"
    assert events["rpc"].context.guild_id == 42

    assert isinstance(events["summarize"], SummarizeCommandRequest)
    assert events["summarize"].hours_argument == "24"
    assert events["summarize"].context.channel_id == 11

    assert isinstance(events["persona"], PersonaCommandRequest)
    assert events["persona"].request_text == "helper hi"
    assert events["persona"].context.user_id == 7

    await provider.shutdown()
    await discord.bot.close()

  asyncio.run(run_test())


def test_provider_requires_configuration():
  discord = DummyDiscord()
  provider = DiscordInputProvider(SimpleNamespace(), discord)

  async def run_test():
    try:
      await provider.startup()
    except RuntimeError:
      await discord.bot.close()
      return
    assert False, "Provider should require handlers"

  asyncio.run(run_test())

