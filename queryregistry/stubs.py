"""Stubbed query registry operations for greenfield domains."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException

from queryregistry.models import DBRequest, DBResponse

StubDispatcher = Callable[[DBRequest], Awaitable[DBResponse]]


def build_stub_dispatchers(label: str) -> dict[tuple[str, str], StubDispatcher]:
  async def _stub(request: DBRequest, *, provider: str) -> DBResponse:
    raise HTTPException(
      status_code=501,
      detail=f"{label} registry operation not implemented",
    )

  return {
    ("create", "1"): _stub,
    ("read", "1"): _stub,
    ("update", "1"): _stub,
    ("delete", "1"): _stub,
    ("list", "1"): _stub,
  }
