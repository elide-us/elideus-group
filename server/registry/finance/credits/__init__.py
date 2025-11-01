"""Finance credits registry helpers.

Requests in this package are described by Pydantic models to guarantee that
service and provider implementations agree on the credit update contract.
"""

from __future__ import annotations

from server.registry.types import DBRequest

from .model import SetCreditsParams

__all__ = [
  "SetCreditsParams",
  "set_credits_request",
]


def _request(name: str, params: SetCreditsParams) -> DBRequest:
  return DBRequest(
    op=f"db:finance:credits:{name}:1",
    payload=params.model_dump(),
  )


def set_credits_request(params: SetCreditsParams) -> DBRequest:
  """Build a ``set`` registry request using validated parameters."""

  return _request("set", params)
