"""Finance query handler package."""

from __future__ import annotations

from server.queryregistry.types import SubdomainDispatcher

from .services import finance_check_status_v1

__all__ = ["DISPATCHERS"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("check_status", "1"): finance_check_status_v1,
}
