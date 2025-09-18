"""Coordinator module for social input providers."""

from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING

from fastapi import FastAPI

from . import BaseModule

if TYPE_CHECKING:  # pragma: no cover
  from .discord_bot_module import DiscordBotModule
  from .providers.social import SocialInputProvider


class SocialInputModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.providers: Dict[str, "SocialInputProvider"] = {}
    self.discord: "DiscordBotModule" | None = None
    self.app.state.social_input = self

  async def startup(self):
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
      self.discord.register_social_input_module(self)
      from .providers.social.discord_input_provider import DiscordInputProvider

      provider = DiscordInputProvider(self, self.discord)
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

  async def register_provider(self, provider: "SocialInputProvider"):
    name = provider.name
    if name in self.providers:
      raise ValueError(f"Provider '{name}' already registered")
    await provider.startup()
    self.providers[name] = provider
    setattr(self.app.state, f"{name}_input_provider", provider)

  async def dispatch(self, provider_name: str, action: str, *args, **kwargs) -> Any:
    provider = self.providers.get(provider_name)
    if not provider:
      raise ValueError(f"Provider '{provider_name}' not registered")
    return await provider.dispatch(action, *args, **kwargs)

  def get_provider(self, name: str) -> "SocialInputProvider | None":
    return self.providers.get(name)
