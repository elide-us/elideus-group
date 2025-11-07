"""Finance query handler package."""

from __future__ import annotations

from .services import finance_check_status_v1

__all__ = ["DISPATCHERS"]

DISPATCHERS = {
  ("check_status", "1"): finance_check_status_v1,
}
