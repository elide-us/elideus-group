"""Finance query handler package."""

from __future__ import annotations

from .status.handler import handle_status_request

__all__ = ["HANDLERS"]

HANDLERS = {
  "status": handle_status_request,
}
