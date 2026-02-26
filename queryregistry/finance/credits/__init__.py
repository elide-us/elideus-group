"""Finance credits query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import SetCreditsParams

__all__ = ["set_credits_request"]


def set_credits_request(params: SetCreditsParams) -> DBRequest:
  return DBRequest(op="db:finance:credits:set:1", payload=params.model_dump())
