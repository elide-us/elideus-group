"""System models registry domain module."""

from typing import Any

from fastapi import FastAPI

from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams
from queryregistry.system.models_registry import (
  delete_model_request,
  list_models_request,
  upsert_model_request,
)
from queryregistry.system.models_registry.models import DeleteModelParams, UpsertModelParams

from . import BaseModule
from .db_module import DbModule


class ModelsRegistryModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.models_registry = self
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def list_models_registry(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_models_request())
    return list(res.rows or [])

  async def upsert_model_registry(self, payload: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertModelParams(**payload)
    await self.db.run(upsert_model_request(params))
    return params.model_dump()

  async def delete_model_registry(self, recid: int | None = None, name: str | None = None) -> dict[str, Any]:
    assert self.db
    params = DeleteModelParams(recid=recid, name=name)
    await self.db.run(delete_model_request(params))
    return params.model_dump()

  async def get_api_providers(self) -> list[str]:
    assert self.db
    res = await self.db.run(get_config_request(ConfigKeyParams(key="ApiProviders")))
    value = res.rows[0]["element_value"] if res.rows else "openai,lumalabs"
    return [p.strip() for p in str(value).split(",") if p.strip()]
