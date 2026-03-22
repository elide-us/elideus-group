"""Identity enablements query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import GetUserEnablementsParams, UpsertUserEnablementsParams

__all__ = ["get_user_enablements_request", "upsert_user_enablements_request"]


def get_user_enablements_request(params: GetUserEnablementsParams) -> DBRequest:
  return DBRequest(op="db:identity:enablements:get:1", payload=params.model_dump())


def upsert_user_enablements_request(params: UpsertUserEnablementsParams) -> DBRequest:
  return DBRequest(op="db:identity:enablements:upsert:1", payload=params.model_dump())
