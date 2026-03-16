"""Finance domain handler implementations."""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

from .accounts.handler import handle_accounts_request
from .credit_lots.handler import handle_credit_lots_request
from .credits.handler import handle_credits_request
from .dimensions.handler import handle_dimensions_request
from .journal_lines.handler import handle_journal_lines_request
from .journals.handler import handle_journals_request
from .numbers.handler import handle_numbers_request
from .periods.handler import handle_periods_request
from .staging.handler import handle_staging_request
from .status.handler import handle_status_request

__all__ = ["handle_finance_request"]

HANDLERS = {
  "accounts": handle_accounts_request,
  "credit_lots": handle_credit_lots_request,
  "credits": handle_credits_request,
  "dimensions": handle_dimensions_request,
  "journal_lines": handle_journal_lines_request,
  "journals": handle_journals_request,
  "numbers": handle_numbers_request,
  "periods": handle_periods_request,
  "staging": handle_staging_request,
  "status": handle_status_request,
}


async def handle_finance_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  if not path:
    raise HTTPException(status_code=404, detail="Unknown finance registry operation")
  subdomain = path[0]
  handler = HANDLERS.get(subdomain)
  if handler is None:
    raise HTTPException(status_code=404, detail="Unknown finance registry operation")
  return await handler(path[1:], request, provider=provider)
