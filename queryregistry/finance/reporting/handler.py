"""Finance reporting subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  credit_lot_summary_v1,
  journal_summary_v1,
  period_status_v1,
  trial_balance_v1,
)

__all__ = ["handle_reporting_request"]

DISPATCHERS = {
  ("trial_balance", "1"): trial_balance_v1,
  ("journal_summary", "1"): journal_summary_v1,
  ("period_status", "1"): period_status_v1,
  ("credit_lot_summary", "1"): credit_lot_summary_v1,
}


async def handle_reporting_request(
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
    detail="Unknown finance reporting operation",
  )
