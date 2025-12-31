"""System links query handler package."""

from __future__ import annotations

from .services import get_home_links_v1, get_navbar_routes_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["DISPATCHERS"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get_home_links", "1"): get_home_links_v1,
  ("get_navbar_routes", "1"): get_navbar_routes_v1,
}
