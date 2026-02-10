"""Assistant persona registry helpers."""

from __future__ import annotations

from server.registry.types import DBRequest

from .model import (
  DeletePersonaParams,
  PersonaRecord,
  PersonaSummary,
  UpsertPersonaParams,
)


_OP_PREFIX = "db:system:personas"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def get_persona_by_name_request(name: str) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), payload={"name": name})


def list_personas_request() -> DBRequest:
  return DBRequest(op=_op("list"), payload={})


def upsert_persona_request(
  *,
  recid: int | None,
  name: str,
  prompt: str,
  tokens: int,
  models_recid: int,
) -> DBRequest:
  return DBRequest(
    op=_op("upsert"),
    payload={
      "recid": recid,
      "name": name,
      "prompt": prompt,
      "tokens": tokens,
      "models_recid": models_recid,
    },
  )


def delete_persona_request(*, recid: int | None = None, name: str | None = None) -> DBRequest:
  return DBRequest(
    op=_op("delete"),
    payload={
      "recid": recid,
      "name": name,
    },
  )
