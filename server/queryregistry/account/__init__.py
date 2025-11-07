"""Account query handler package."""

from __future__ import annotations

from .services import account_check_status_v1

__all__ = ["DISPATCHERS"]

DISPATCHERS = {
  ("check_status", "1"): account_check_status_v1,
}
