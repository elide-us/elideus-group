"""Account-domain MSSQL helpers for user records."""

from __future__ import annotations

from typing import Any

from server.registry.support.users.mssql import set_credits_v1 as _support_set_credits_v1

__all__ = [
  "set_credits_v1",
]


# Delegate to the support-domain implementation to avoid duplication.
def set_credits_v1(args: dict[str, Any]):
  return _support_set_credits_v1(args)
