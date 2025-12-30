"""System configuration query handler package."""

from __future__ import annotations

from .services import system_check_status_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["DISPATCHERS"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("check_status", "1"): system_check_status_v1,
}
