from __future__ import annotations
import logging, asyncio
from fastapi import FastAPI
from openai import AsyncOpenAI
from . import BaseModule
from .db_module import DbModule


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

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
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

  async def fetch_chat(self, schemas: list, role: str, prompt: str, tokens: int, prompt_context: str = ""):
    if not self.client:
      logging.warning("[OpenaiModule] client not initialized")
      return {"content": ""}
    messages = [{"role": "system", "content": role}]
    if prompt_context:
      messages.append({"role": "user", "content": prompt_context})
    messages.append({"role": "user", "content": prompt})
    completion = await self.client.chat.completions.create(
      model="gpt-4o-mini",
      max_tokens=tokens,
      tools=schemas,
      messages=messages,
    )
    return {"content": completion.choices[0].message.content}
