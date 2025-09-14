from __future__ import annotations
import logging
from fastapi import FastAPI
from openai import AsyncOpenAI
from . import BaseModule
from .db_module import DbModule

class OpenaiModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.client: AsyncOpenAI | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.client = await self.init_openai_client()
    self.app.state.openai = self
    logging.info("[OpenaiModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[OpenaiModule] shutdown")
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
