"""Finance credits query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import GetCreditsParams, SetCreditsParams

__all__ = ["get_credits_request", "set_credits_request"]


def get_credits_request(params: GetCreditsParams) -> DBRequest:
  return DBRequest(op="db:finance:credits:get:1", payload=params.model_dump())


def set_credits_request(params: SetCreditsParams) -> DBRequest:
  return DBRequest(op="db:finance:credits:set:1", payload=params.model_dump())
