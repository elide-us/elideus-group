from __future__ import annotations

import logging

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule
from .openai_module import OpenaiModule


class PersonasModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.openai: OpenaiModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.openai = getattr(self.app.state, "openai", None)
    if self.openai:
      await self.openai.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None
    self.openai = None

  async def _get_persona(self, name: str) -> dict | None:
    if not self.db:
      return None
    try:
      res = await self.db.run("db:assistant:personas:get_by_name:1", {"name": name})
    except Exception:
      logging.exception("[PersonasModule] failed to fetch persona", extra={"persona": name})
      return None
    if res.rows:
      return res.rows[0]
    return None

  async def persona_response(
    self,
    persona: str,
    message: str,
    *,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
  ) -> dict:
    persona_name = (persona or "").strip()
    if not persona_name:
      raise ValueError("persona is required")
    prompt = (message or "").strip()
    if not prompt:
      raise ValueError("message is required")

    persona_row = await self._get_persona(persona_name)
    if not persona_row:
      raise ValueError(f"persona '{persona_name}' was not found")

    instructions = persona_row.get("element_prompt") or ""
    if not instructions:
      raise ValueError(f"persona '{persona_name}' is missing instructions")

    tokens = persona_row.get("element_tokens")
    model_hint = persona_row.get("element_model")

    if not self.openai or not getattr(self.openai, "client", None):
      logging.warning("[PersonasModule] OpenAI module not available", extra={"persona": persona_name})
      return {
        "persona": persona_name,
        "response_text": "[[STUB: persona response here]]",
        "model": model_hint,
        "role": instructions,
      }

    await self.openai.on_ready()
    generator = getattr(self.openai, "generate_chat", None)
    if generator:
      response = await generator(
        system_prompt=instructions,
        user_prompt=prompt,
        max_tokens=tokens,
        persona=persona_name,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        input_log=prompt,
      )
    else:
      response = await self.openai.fetch_chat(
        [],
        instructions,
        prompt,
        tokens,
        persona=persona_name,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        input_log=prompt,
      )
    if isinstance(response, dict):
      content = response.get("content", "")
      model_value = response.get("model")
      role_value = response.get("role", "")
    else:
      content = getattr(response, "content", "")
      model_value = getattr(response, "model", None)
      role_value = getattr(response, "role", "")
    return {
      "persona": persona_name,
      "response_text": content,
      "model": model_value,
      "role": role_value,
    }
