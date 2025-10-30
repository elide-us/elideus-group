"""Assistant persona registry helpers."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from .model import (
  DeletePersonaParams,
  PersonaRecord,
  PersonaSummary,
  UpsertPersonaParams,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "delete_persona_request",
  "get_persona_by_name_request",
  "list_personas_request",
  "register",
  "upsert_persona_request",
  "DeletePersonaParams",
  "PersonaRecord",
  "PersonaSummary",
  "UpsertPersonaParams",
]

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


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="delete", version=1, implementation="delete_persona")
  register_op(name="get_by_name", version=1)
  register_op(name="list", version=1, implementation="list_personas")
  register_op(name="upsert", version=1, implementation="upsert_persona")
