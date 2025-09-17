from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List
from fastapi import FastAPI
from openai import AsyncOpenAI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule

if TYPE_CHECKING:  # pragma: no cover
  from .discord_output_module import DiscordOutputModule


class SummaryQueue:
  def __init__(self, delay=15):
    self.queue = asyncio.Queue()
    self._lock = asyncio.Lock()
    self.delay = delay
    self.processing = False
    self._processing_task: asyncio.Task | None = None

  async def add(self, func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    async with self._lock:
      await self.queue.put((func, args, kwargs, future))
      if not self.processing:
        self.processing = True
        self._processing_task = loop.create_task(self._process_queue())
    return await future

  async def _process_queue(self):
    loop = asyncio.get_running_loop()
    try:
      while True:
        func, args, kwargs, future = await self.queue.get()
        try:
          result = await func(*args, **kwargs)
          if not future.done():
            future.set_result(result)
        except Exception as e:
          if not future.done():
            future.set_exception(e)
        await asyncio.sleep(self.delay)
    except asyncio.CancelledError:
      raise
    finally:
      async with self._lock:
        self.processing = False
        self._processing_task = None
        if not self.queue.empty():
          self.processing = True
          self._processing_task = loop.create_task(self._process_queue())

class OpenaiModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.client: AsyncOpenAI | None = None
    self.summary_queue = SummaryQueue()
    self.discord: DiscordBotModule | None = None
    self.discord_output: "DiscordOutputModule" | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord_bot", None) or getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.discord_output = getattr(self.app.state, "discord_output", None)
    if self.discord_output:
      await self.discord_output.on_ready()
    self.client = await self.init_openai_client()
    self.app.state.openai = self
    logging.info("[OpenaiModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[OpenaiModule] shutdown")
    if self.summary_queue._processing_task:
      self.summary_queue._processing_task.cancel()
    self.client = None
    self.db = None
    self.discord_output = None

  async def get_openai_token(self) -> str:
    assert self.db
    res = await self.db.run("db:system:config:get_config:1", {"key": "OpenAIApiKey"})
    if res.rows:
      return res.rows[0].get("value", "")
    return ""

  async def init_openai_client(self) -> AsyncOpenAI | None:
    token = await self.get_openai_token()
    if not token:
      logging.warning("[OpenaiModule] OpenAIApiKey not configured")
      return None
    return AsyncOpenAI(api_key=token)

  async def _get_persona(self, name: str) -> dict | None:
    if not self.db:
      return None
    try:
      res = await self.db.run("db:assistant:personas:get_by_name:1", {"name": name})
      if res.rows:
        return res.rows[0]
    except Exception:
      logging.exception("[OpenaiModule] fetch persona failed")
    return None

  async def get_persona_definition(self, name: str) -> Dict[str, Any] | None:
    persona_row = await self._get_persona(name)
    if not persona_row:
      return None
    prompt = persona_row.get("prompt") or persona_row.get("element_prompt") or ""
    tokens_val = persona_row.get("tokens")
    if tokens_val is None:
      tokens_val = persona_row.get("element_tokens")
    models_recid = persona_row.get("models_recid")
    if models_recid is None:
      models_recid = persona_row.get("element_models_recid")
    model_hint = persona_row.get("model") or persona_row.get("element_model")
    return {
      "recid": persona_row.get("recid"),
      "name": persona_row.get("name", ""),
      "prompt": prompt,
      "tokens": int(tokens_val or 0),
      "models_recid": int(models_recid) if models_recid is not None else None,
      "model": model_hint,
    }

  async def list_models(self) -> List[Dict[str, Any]]:
    assert self.db
    res = await self.db.run("db:assistant:models:list:1", {})
    return list(res.rows or [])

  async def list_personas(self) -> List[Dict[str, Any]]:
    assert self.db
    res = await self.db.run("db:assistant:personas:list:1", {})
    personas: List[Dict[str, Any]] = []
    for row in res.rows or []:
      personas.append({
        "recid": row.get("recid"),
        "name": row.get("name", ""),
        "prompt": row.get("prompt", ""),
        "tokens": int(row.get("tokens", 0) or 0),
        "models_recid": (
          int(row.get("models_recid")) if row.get("models_recid") is not None else None
        ),
        "model": row.get("model"),
      })
    return personas

  async def upsert_persona(self, persona: Dict[str, Any]) -> None:
    assert self.db
    model_recid = persona.get("models_recid")
    if model_recid is None:
      raise ValueError("models_recid required")
    payload = {
      "recid": persona.get("recid"),
      "name": persona.get("name", ""),
      "prompt": persona.get("prompt", ""),
      "tokens": int(persona.get("tokens", 0) or 0),
      "models_recid": int(model_recid),
    }
    if not payload["name"]:
      raise ValueError("name required")
    await self.db.run("db:assistant:personas:upsert:1", payload)

  async def delete_persona(self, recid: int | None = None, name: str | None = None) -> None:
    assert self.db
    await self.db.run(
      "db:assistant:personas:delete:1",
      {"recid": recid, "name": name},
    )

  async def _log_conversation_start(
    self,
    personas_recid: int | None,
    models_recid: int | None,
    guild_id: int | None,
    channel_id: int | None,
    user_id: int | None,
    input_data: str,
    tokens: int | None,
  ) -> int | None:
    if not self.db or personas_recid is None or models_recid is None:
      return None
    try:
      guild_id_str = str(guild_id) if guild_id is not None else None
      channel_id_str = str(channel_id) if channel_id is not None else None
      user_id_str = str(user_id) if user_id is not None else None
      existing = await self.db.run(
        "db:assistant:conversations:find_recent:1",
        {
          "personas_recid": personas_recid,
          "models_recid": models_recid,
          "guild_id": guild_id_str,
          "channel_id": channel_id_str,
          "user_id": user_id_str,
          "input_data": input_data,
        },
      )
      if existing.rows:
        recid = existing.rows[0].get("recid")
        if recid is not None:
          return recid
      res = await self.db.run(
        "db:assistant:conversations:insert:1",
        {
          "personas_recid": personas_recid,
          "models_recid": models_recid,
          "guild_id": guild_id_str,
          "channel_id": channel_id_str,
          "user_id": user_id_str,
          "input_data": input_data,
          "output_data": "",
          "tokens": tokens,
        },
      )
      if res.rows:
        return res.rows[0].get("recid")
    except Exception:
      logging.exception("[OpenaiModule] insert conversation failed")
    return None

  async def _log_conversation_end(
    self,
    recid: int,
    output_data: str,
    tokens: int | None,
  ):
    if not self.db:
      return
    try:
      res = await self.db.run(
        "db:assistant:conversations:update_output:1",
        {"recid": recid, "output_data": output_data, "tokens": tokens},
      )
      if res.rowcount == 0:
        logging.warning(
          "[OpenaiModule] conversation update affected 0 rows (recid=%s)",
          recid,
        )
    except Exception:
      logging.exception("[OpenaiModule] update conversation failed")

  async def generate_chat(
    self,
    *,
    system_prompt: str,
    user_prompt: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    tools: List[Dict[str, Any]] | None = None,
    prompt_context: str = "",
    persona: str | None = None,
    persona_details: Dict[str, Any] | None = None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
    input_log: str | None = None,
    token_count: int | None = None,
  ) -> Dict[str, Any]:
    if not self.client:
      logging.warning("[OpenaiModule] client not initialized")
      return {"content": ""}

    conv_id = None
    personas_recid = None
    models_recid = None
    resolved_model = (model or "").strip() or "gpt-4o-mini"
    resolved_tokens = max_tokens
    resolved_prompt = system_prompt or ""
    resolved_persona_details: Dict[str, Any] | None = persona_details

    if persona:
      if resolved_persona_details is None:
        try:
          resolved_persona_details = await self.get_persona_definition(persona)
        except Exception:
          logging.exception(
            "[OpenaiModule] failed to resolve persona details",
            extra={"persona": persona},
          )
          resolved_persona_details = None
      if resolved_persona_details:
        personas_recid = resolved_persona_details.get("recid")
        models_recid = resolved_persona_details.get("models_recid")
        persona_model = resolved_persona_details.get("model")
        if persona_model:
          resolved_model = persona_model
        persona_tokens = resolved_persona_details.get("tokens")
        if resolved_tokens is None and persona_tokens is not None:
          resolved_tokens = int(persona_tokens)
        persona_prompt = resolved_persona_details.get("prompt")
        if not resolved_prompt and persona_prompt:
          resolved_prompt = persona_prompt

    if resolved_tokens is None:
      resolved_tokens = 64

    if persona and personas_recid is not None and models_recid is not None:
      conv_id = await self._log_conversation_start(
        personas_recid,
        models_recid,
        guild_id,
        channel_id,
        user_id,
        input_log or (user_prompt or ""),
        token_count,
      )

    messages: List[Dict[str, str]] = []
    if resolved_prompt:
      messages.append({"role": "system", "content": resolved_prompt})
    if prompt_context:
      messages.append({"role": "user", "content": prompt_context})
    if user_prompt:
      messages.append({"role": "user", "content": user_prompt})
    if not messages:
      raise ValueError("No content provided for chat generation")

    params: Dict[str, Any] = {
      "model": resolved_model,
      "messages": messages,
    }
    if resolved_tokens is not None:
      params["max_tokens"] = resolved_tokens
    if tools:
      params["tools"] = tools

    completion = await self.client.chat.completions.create(**params)
    usage = getattr(completion, "usage", None)
    total_tokens = getattr(usage, "total_tokens", None) if usage else None
    choice = completion.choices[0].message
    content = choice.content
    result: Dict[str, Any] = {
      "content": content,
      "model": getattr(completion, "model", resolved_model),
      "role": getattr(choice, "role", ""),
    }
    if usage:
      result["usage"] = {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": total_tokens,
      }
    if conv_id:
      await self._log_conversation_end(conv_id, content, total_tokens)
    return result

  async def persona_response(
    self,
    persona: str,
    message: str,
    *,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
  ) -> Dict[str, Any]:
    persona_name = (persona or "").strip()
    if not persona_name:
      raise ValueError("persona is required")
    prompt = (message or "").strip()
    if not prompt:
      raise ValueError("message is required")

    persona_details = await self.get_persona_definition(persona_name)
    if not persona_details:
      raise ValueError(f"persona '{persona_name}' was not found")

    instructions = (persona_details.get("prompt") or "").strip()
    if not instructions:
      raise ValueError(f"persona '{persona_name}' is missing instructions")

    tokens = persona_details.get("tokens")
    model_hint = persona_details.get("model")
    resolved_name = (persona_details.get("name") or persona_name).strip() or persona_name

    if not self.client:
      logging.warning(
        "[OpenaiModule] client not initialized for persona response",
        extra={"persona": persona_name},
      )
      return {
        "persona": resolved_name,
        "response_text": "[[STUB: persona response here]]",
        "model": model_hint or "",
        "role": instructions,
      }

    response = await self.generate_chat(
      system_prompt=instructions,
      user_prompt=prompt,
      model=model_hint,
      max_tokens=tokens,
      persona=persona_name,
      persona_details=persona_details,
      guild_id=guild_id,
      channel_id=channel_id,
      user_id=user_id,
      input_log=prompt,
      token_count=None,
    )

    content = response.get("content", "")
    model_value = response.get("model") or model_hint
    role_value = response.get("role", "") or instructions
    return {
      "persona": resolved_name,
      "response_text": content,
      "model": model_value,
      "role": role_value,
    }

  async def fetch_chat(
    self,
    schemas: list,
    role: str,
    prompt: str,
    tokens: int | None,
    prompt_context: str = "",
    *,
    persona: str | None = None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    user_id: int | None = None,
    input_log: str | None = None,
    token_count: int | None = None,
    model: str = "gpt-4o-mini",
  ):
    result = await self.generate_chat(
      system_prompt=role,
      user_prompt=prompt,
      model=model,
      max_tokens=tokens,
      tools=schemas,
      prompt_context=prompt_context,
      persona=persona,
      guild_id=guild_id,
      channel_id=channel_id,
      user_id=user_id,
      input_log=input_log,
      token_count=token_count,
    )
    if isinstance(result, dict):
      result.pop("usage", None)
    return result
