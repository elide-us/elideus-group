"""System query handler package."""

from __future__ import annotations

from server.queryregistry.types import SubdomainDispatcher

from .services import system_check_status_v1

__all__ = ["DISPATCHERS"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("check_status", "1"): system_check_status_v1,
}
