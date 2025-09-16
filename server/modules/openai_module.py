from __future__ import annotations
import logging, asyncio
from fastapi import FastAPI
from openai import AsyncOpenAI
from . import BaseModule
from .db_module import DbModule
from .discord_module import DiscordModule


async def send_to_discord(channel, text: str, max_message_size: int = 1998, delay: float = 1.0):
  for block in text.split("\n"):
    if not block.strip() or block.strip() == "---":
      continue
    start = 0
    while start < len(block):
      end = min(start + max_message_size, len(block))
      if end < len(block) and block[end] != ' ':
        end = block.rfind(' ', start, end)
        if end == -1:
          end = start + max_message_size
      chunk = block[start:end].strip()
      if chunk:
        await channel.send(chunk)
        await asyncio.sleep(delay)
      start = end


async def send_to_discord_user(user, text: str, max_message_size: int = 1998, delay: float = 1.0):
  for block in text.split("\n"):
    if not block.strip() or block.strip() == "---":
      continue
    start = 0
    while start < len(block):
      end = min(start + max_message_size, len(block))
      if end < len(block) and block[end] != ' ':
        end = block.rfind(' ', start, end)
        if end == -1:
          end = start + max_message_size
      chunk = block[start:end].strip()
      if chunk:
        await user.send(chunk)
        await asyncio.sleep(delay)
      start = end


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
    try:
      while not self.queue.empty():
        func, args, kwargs, future = await self.queue.get()
        try:
          result = await func(*args, **kwargs)
          future.set_result(result)
        except Exception as e:
          future.set_exception(e)
        await asyncio.sleep(self.delay)
    except asyncio.CancelledError:
      raise
    finally:
      async with self._lock:
        self.processing = False

class OpenaiModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.client: AsyncOpenAI | None = None
    self.summary_queue = SummaryQueue()
    self.discord: DiscordModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
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
      res = await self.db.run(
        "db:assistant:conversations:insert:1",
        {
          "personas_recid": personas_recid,
          "models_recid": models_recid,
          "guild_id": str(guild_id) if guild_id is not None else None,
          "channel_id": str(channel_id) if channel_id is not None else None,
          "user_id": str(user_id) if user_id is not None else None,
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
    if not self.client:
      logging.warning("[OpenaiModule] client not initialized")
      return {"content": ""}
    conv_id = None
    personas_recid = None
    models_recid = None
    if persona:
      persona_row = await self._get_persona(persona)
      if persona_row:
        personas_recid = persona_row.get("recid")
        models_recid = persona_row.get("models_recid")
        model = persona_row.get("element_model", model)
        if tokens is None:
          tokens = persona_row.get("element_tokens")
    if tokens is None:
      tokens = 64
    if persona and personas_recid is not None and models_recid is not None:
      conv_id = await self._log_conversation_start(
        personas_recid,
        models_recid,
        guild_id,
        channel_id,
        user_id,
        input_log or prompt,
        token_count,
      )
    messages = [{"role": "system", "content": role}]
    if prompt_context:
      messages.append({"role": "user", "content": prompt_context})
    messages.append({"role": "user", "content": prompt})
    params = {
      "model": model,
      "max_tokens": tokens,
      "messages": messages,
    }
    if schemas:
      params["tools"] = schemas
    completion = await self.client.chat.completions.create(**params)
    usage = getattr(completion, "usage", None)
    total_tokens = getattr(usage, "total_tokens", None) if usage else None
    choice = completion.choices[0].message
    content = choice.content
    result = {
      "content": content,
      "model": getattr(completion, "model", ""),
      "role": getattr(choice, "role", ""),
    }
    if conv_id:
      await self._log_conversation_end(conv_id, content, total_tokens)
    return result
