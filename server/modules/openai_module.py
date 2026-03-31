from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List
from fastapi import FastAPI
from openai import AsyncOpenAI
from . import BaseModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams
from queryregistry.system.conversations import (
  insert_message_request,
  list_by_time_request,
  list_channel_messages_request,
  list_thread_request,
)
from queryregistry.system.conversations.models import (
  InsertMessageParams,
  ListByTimeParams,
  ListChannelMessagesParams,
  ListThreadParams,
)
from queryregistry.system.personas import list_models_request
from queryregistry.system.personas import (
  delete_persona_request,
  get_persona_by_name_request,
  list_personas_request,
  upsert_persona_request,
)
from queryregistry.system.personas.models import (
  DeletePersonaParams,
  PersonaNameParams,
  UpsertPersonaParams,
)

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
    logging.debug("[OpenaiModule] loaded")
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
    res = await self.db.run(get_config_request(ConfigKeyParams(key="OpenAIApiKey")))
    if res.rows:
      return res.rows[0].get("element_value", "")
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
      res = await self.db.run(get_persona_by_name_request(PersonaNameParams(name=name)))
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
    res = await self.db.run(list_models_request())
    return list(res.rows or [])

  async def list_personas(self) -> List[Dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_personas_request())
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
        "is_active": bool(row.get("is_active", row.get("element_is_active", True))),
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
      "is_active": bool(persona.get("is_active", True)),
    }
    if not payload["name"]:
      raise ValueError("name required")
    await self.db.run(
      upsert_persona_request(UpsertPersonaParams(
        recid=payload["recid"],
        name=payload["name"],
        prompt=payload["prompt"],
        tokens=payload["tokens"],
        models_recid=payload["models_recid"],
        is_active=payload["is_active"],
      ))
    )

  async def delete_persona(self, recid: int | None = None, name: str | None = None) -> None:
    assert self.db
    await self.db.run(delete_persona_request(DeletePersonaParams(recid=recid, name=name)))

  async def log_message(
    self,
    *,
    personas_recid: int,
    models_recid: int,
    role: str,
    content: str,
    guild_id: int | str | None = None,
    channel_id: int | str | None = None,
    user_id: int | str | None = None,
    users_guid: str | None = None,
    thread_id: str | None = None,
    tokens: int | None = None,
  ) -> int | None:
    """Insert a single message row using the new message-per-row schema."""
    if not self.db:
      return None
    try:
      res = await self.db.run(
        insert_message_request(InsertMessageParams(
          personas_recid=personas_recid,
          models_recid=models_recid,
          role=role,
          content=content,
          guild_id=str(guild_id) if guild_id is not None else None,
          channel_id=str(channel_id) if channel_id is not None else None,
          user_id=str(user_id) if user_id is not None else None,
          users_guid=users_guid,
          thread_id=thread_id,
          tokens=tokens,
        ))
      )
      if res.rows:
        return res.rows[0].get("recid")
    except Exception:
      logging.exception("[OpenaiModule] insert message failed")
    return None

  async def get_thread_history(
    self,
    thread_id: str,
    *,
    limit: int = 20,
  ) -> List[Dict[str, str]]:
    """Retrieve message history for a thread, formatted for OpenAI messages."""
    if not self.db or not thread_id:
      return []
    try:
      res = await self.db.run(
        list_thread_request(ListThreadParams(thread_id=thread_id))
      )
    except Exception:
      logging.exception("[OpenaiModule] failed to load thread history")
      return []
    rows = list(res.rows or [])
    if limit and limit > 0:
      rows = rows[-limit:]
    messages: List[Dict[str, str]] = []
    for row in rows:
      role = (row.get("element_role") or "user").strip()
      content = (row.get("element_content") or "").strip()
      if content:
        messages.append({"role": role, "content": content})
    return messages

  async def get_channel_context(
    self,
    guild_id: int | str,
    channel_id: int | str,
    *,
    limit: int = 30,
  ) -> List[Dict[str, str]]:
    """Retrieve recent stored messages from a guild+channel for context."""
    if not self.db:
      return []
    try:
      res = await self.db.run(
        list_channel_messages_request(ListChannelMessagesParams(
          guild_id=str(guild_id),
          channel_id=str(channel_id),
          limit=limit,
        ))
      )
    except Exception:
      logging.exception("[OpenaiModule] failed to load channel context")
      return []
    rows = list(res.rows or [])
    rows.reverse()
    messages: List[Dict[str, str]] = []
    for row in rows:
      role = (row.get("element_role") or "user").strip()
      content = (row.get("element_content") or "").strip()
      if content:
        messages.append({"role": role, "content": content})
    return messages

  async def get_recent_persona_conversation_history(
    self,
    personas_recid: int,
    *,
    lookback_days: int = 30,
    limit: int = 5,
  ) -> List[Dict[str, str]]:
    if not self.db:
      return []
    if personas_recid is None:
      return []
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=max(lookback_days, 0))
    try:
      res = await self.db.run(
        list_by_time_request(ListByTimeParams(
          personas_recid=personas_recid,
          start=start.isoformat(),
          end=end.isoformat(),
        ))
      )
    except Exception:
      logging.exception("[OpenaiModule] failed to load persona conversation history")
      raise

    rows = list(res.rows or [])

    def _parse_timestamp(value: Any) -> datetime:
      if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
      if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
      if isinstance(value, str):
        candidate = value.replace("Z", "+00:00")
        try:
          return datetime.fromisoformat(candidate)
        except ValueError:
          pass
      return datetime.min.replace(tzinfo=timezone.utc)

    rows.sort(key=lambda row: _parse_timestamp(row.get("element_created_on")))
    if limit and limit > 0:
      rows = rows[-limit:]

    conversation_history: List[Dict[str, str]] = []
    for row in rows:
      user_input = (row.get("element_input") or "").strip()
      if user_input:
        conversation_history.append({"role": "user", "content": user_input})
      assistant_output = (row.get("element_output") or "").strip()
      if assistant_output:
        conversation_history.append({"role": "assistant", "content": assistant_output})

    return conversation_history

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

  async def action_gather_stored_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    payload = input_data.get("payload") or {}
    context = input_data.get("context") or {}
    personas_recid = context.get("personas_recid")
    guild_id = payload.get("guild_id")
    channel_id = payload.get("channel_id")
    if personas_recid is None:
      raise ValueError("context.personas_recid is required")
    if guild_id is None or channel_id is None:
      raise ValueError("payload.guild_id and payload.channel_id are required")
    conversation_history = await self.get_recent_persona_conversation_history(int(personas_recid))
    stored_channel_context = await self.get_channel_context(int(guild_id), int(channel_id))
    return {
      "context": {
        "conversation_history": conversation_history,
        "stored_channel_context": stored_channel_context,
      }
    }

  async def action_generate_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    payload = input_data.get("payload") or {}
    context = input_data.get("context") or {}
    persona_name = str(payload.get("persona") or "").strip()
    message = str(payload.get("message") or "").strip()
    if not persona_name:
      raise ValueError("payload.persona is required")
    if not message:
      raise ValueError("payload.message is required")

    persona_details = context.get("persona_details") or {}
    system_prompt = str(persona_details.get("prompt") or "").strip()
    if not system_prompt:
      raise ValueError(f"persona '{persona_name}' is missing instructions")

    thread_id = str(context.get("thread_id") or f"persona:{persona_name}:{datetime.now(timezone.utc).isoformat()}")
    conversation_history = context.get("conversation_history") or []
    stored_channel_context = context.get("stored_channel_context") or []
    channel_history = context.get("channel_history") or []
    history_lines = []

    def _extend_history(items: Any):
      if not isinstance(items, list):
        return
      for item in items:
        if isinstance(item, dict):
          role = str(item.get("role") or item.get("author") or "user").strip()
          content = str(item.get("content") or "").strip()
          if content:
            history_lines.append(f"{role}: {content}")

    _extend_history(conversation_history)
    _extend_history(stored_channel_context)
    _extend_history(channel_history)
    prompt_context = "\n".join(history_lines)

    response = await self.generate_chat(
      system_prompt=system_prompt,
      user_prompt=message,
      model=context.get("model"),
      max_tokens=context.get("max_tokens"),
      prompt_context=prompt_context,
      persona=persona_name,
      persona_details=persona_details,
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      input_log=message,
    )

    response_text = str(response.get("content") or "")
    model_used = response.get("model") or context.get("model")
    usage = response.get("usage")
    personas_recid = context.get("personas_recid")
    models_recid = context.get("models_recid")
    if personas_recid is None or models_recid is None:
      raise ValueError("context.personas_recid and context.models_recid are required")

    await self.log_message(
      personas_recid=int(personas_recid),
      models_recid=int(models_recid),
      role="user",
      content=message,
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      thread_id=thread_id,
    )
    await self.log_message(
      personas_recid=int(personas_recid),
      models_recid=int(models_recid),
      role="assistant",
      content=response_text,
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      thread_id=thread_id,
      tokens=(usage or {}).get("total_tokens") if isinstance(usage, dict) else None,
    )

    return {
      "context": {
        "response_text": response_text,
        "model_used": model_used,
        "thread_id": thread_id,
        "usage": usage,
      }
    }
