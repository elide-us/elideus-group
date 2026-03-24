"""Finance credit lots subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  consume_credits_v1,
  create_event_v1,
  create_lot_v1,
  expire_lot_v1,
  get_lot_v1,
  list_events_by_lot_v1,
  list_lots_by_user_v1,
  sum_remaining_by_user_v1,
)

__all__ = ["handle_credit_lots_request"]

DISPATCHERS = {
  ("list_lots_by_user", "1"): list_lots_by_user_v1,
  ("get_lot", "1"): get_lot_v1,
  ("create_lot", "1"): create_lot_v1,
  ("consume_credits", "1"): consume_credits_v1,
  ("expire_lot", "1"): expire_lot_v1,
  ("list_events_by_lot", "1"): list_events_by_lot_v1,
  ("create_event", "1"): create_event_v1,
  ("sum_remaining_by_user", "1"): sum_remaining_by_user_v1,
}


async def handle_credit_lots_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown finance credit lots operation",
  )
