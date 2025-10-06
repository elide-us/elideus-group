"""Assistant persona registry helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "delete_persona_request",
  "get_persona_by_name_request",
  "list_personas_request",
  "register",
  "upsert_persona_request",
]

_OP_PREFIX = "db:system:assistant.personas"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def get_persona_by_name_request(name: str) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), params={"name": name})


def list_personas_request() -> DBRequest:
  return DBRequest(op=_op("list"), params={})


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
    params={
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
    params={
      "recid": recid,
      "name": name,
    },
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function("delete", version=1, implementation="delete_persona")
  router.add_function("get_by_name", version=1)
  router.add_function("list", version=1, implementation="list_personas")
  router.add_function("upsert", version=1, implementation="upsert_persona")
