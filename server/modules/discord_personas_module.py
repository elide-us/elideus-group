from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI

from server.modules import BaseModule
from server.modules.openai_module import OpenaiModule


class DiscordPersonasModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.openai: OpenaiModule | None = None

  async def startup(self):
    self.openai = getattr(self.app.state, "openai", None)
    if self.openai:
      await self.openai.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.openai = None

  async def list_models(self) -> List[Dict[str, Any]]:
    if not self.openai:
      return []
    return await self.openai.list_models()

  async def list_personas(self) -> List[Dict[str, Any]]:
    if not self.openai:
      return []
    return await self.openai.list_personas()

  async def upsert_persona(self, persona: Dict[str, Any]) -> None:
    if not self.openai:
      raise RuntimeError("OpenAI module is not available")
    await self.openai.upsert_persona(persona)

  async def delete_persona(self, recid: int | None = None, name: str | None = None) -> None:
    if not self.openai:
      raise RuntimeError("OpenAI module is not available")
    await self.openai.delete_persona(recid=recid, name=name)
