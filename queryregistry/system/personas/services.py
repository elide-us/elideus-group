"""System personas query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  DeleteModelParams,
  DeletePersonaParams,
  ModelNameParams,
  PersonaNameParams,
  UpsertModelParams,
  UpsertPersonaParams,
)

__all__ = [
  "delete_persona_v1",
  "get_by_name_v1",
  "list_personas_v1",
  "models_delete_v1",
  "models_get_by_name_v1",
  "models_list_v1",
  "models_upsert_v1",
  "upsert_persona_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_GET_BY_NAME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_by_name_v1}
_LIST_PERSONAS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_personas_v1}
_UPSERT_PERSONA_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_persona_v1}
_DELETE_PERSONA_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_persona_v1}
_MODELS_LIST_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.models_list_v1}
_MODELS_GET_BY_NAME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.models_get_by_name_v1}
_MODELS_UPSERT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.models_upsert_v1}
_MODELS_DELETE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.models_delete_v1}


class _ListPersonasParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class _ListModelsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system personas registry")
  return dispatcher


async def get_by_name_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = PersonaNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_BY_NAME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_personas_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = _ListPersonasParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_PERSONAS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_persona_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertPersonaParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_PERSONA_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_persona_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeletePersonaParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_PERSONA_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def models_list_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = _ListModelsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _MODELS_LIST_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def models_get_by_name_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ModelNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _MODELS_GET_BY_NAME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def models_upsert_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertModelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _MODELS_UPSERT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def models_delete_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteModelParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _MODELS_DELETE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
