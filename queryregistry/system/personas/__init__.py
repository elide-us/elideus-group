"""System personas query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeletePersonaParams, PersonaNameParams, UpsertPersonaParams

__all__ = [
  "delete_persona_request",
  "get_persona_by_name_request",
  "list_personas_request",
  "upsert_persona_request",
]


def get_persona_by_name_request(params: PersonaNameParams) -> DBRequest:
  return DBRequest(op="db:system:personas:get_by_name:1", payload=params.model_dump())


def list_personas_request() -> DBRequest:
  return DBRequest(op="db:system:personas:list:1", payload={})


def upsert_persona_request(params: UpsertPersonaParams) -> DBRequest:
  return DBRequest(op="db:system:personas:upsert:1", payload=params.model_dump())


def delete_persona_request(params: DeletePersonaParams) -> DBRequest:
  return DBRequest(op="db:system:personas:delete:1", payload=params.model_dump())
