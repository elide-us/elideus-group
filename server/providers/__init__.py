# server/providers/__init__.py

from abc import ABC, abstractmethod
from fastapi import FastAPI


# === Base Class ===

class Provider(ABC):
    def __init__(self, app: FastAPI):
        self.app = app

    @abstractmethod
    async def startup(self):
        pass

    @abstractmethod
    async def shutdown(self):
        pass

# === Registry ===

from server.providers.database_provider import DatabaseProvider
from server.providers.openai_provider import OpenAIProvider
from server.providers.discord_provider import DiscordProvider

class ProviderRegistry:
    def __init__(self, app: FastAPI):
        self.app = app
        self.providers: dict[str, Provider] = {}

        self._register("openai", OpenAIProvider)
        self._register("discord", DiscordProvider)
        self._register("database", DatabaseProvider)

    def _register(self, name: str, provider_cls: type[Provider]):
        instance = provider_cls(self.app)
        self.providers[name] = instance
        setattr(self.app.state, f"{name}_provider", instance)

    async def startup(self):
        for provider in self.providers.values():
            await provider.startup()

    async def shutdown(self):
        for provider in self.providers.values():
            await provider.shutdown()

