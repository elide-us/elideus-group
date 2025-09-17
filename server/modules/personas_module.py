from __future__ import annotations

import logging

from fastapi import FastAPI

from . import BaseModule
from .openai_module import OpenaiModule


class PersonasModule(BaseModule):
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

    if not self.openai:
      logging.warning("[PersonasModule] OpenAI module not available", extra={"persona": persona_name})
      return {
        "persona": persona_name,
        "response_text": "[[STUB: persona response here]]",
        "model": "",
        "role": "",
      }

    await self.openai.on_ready()
    persona_details = await self.openai.get_persona_definition(persona_name)
    if not persona_details:
      raise ValueError(f"persona '{persona_name}' was not found")

    instructions = persona_details.get("prompt", "")
    if not instructions:
      raise ValueError(f"persona '{persona_name}' is missing instructions")

    tokens = persona_details.get("tokens")
    model_hint = persona_details.get("model")
    persona_recid = persona_details.get("recid")
    models_recid = persona_details.get("models_recid")

    if not getattr(self.openai, "client", None):
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
