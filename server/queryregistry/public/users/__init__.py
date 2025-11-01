"""Public users query handlers."""

from __future__ import annotations

from server.queryregistry.types import SubdomainDispatcher

from .services import public_users_check_status_v1

__all__ = ["DISPATCHERS"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("check_status", "1"): public_users_check_status_v1,
}
