"""System public_vars query handler package."""

from __future__ import annotations

from .services import get_hostname_v1, get_repo_v1, get_version_v1
from ..dispatch import SubdomainDispatcher

__all__ = ["DISPATCHERS"]

DISPATCHERS: dict[tuple[str, str], SubdomainDispatcher] = {
  ("get_version", "1"): get_version_v1,
  ("get_hostname", "1"): get_hostname_v1,
  ("get_repo", "1"): get_repo_v1,
}
