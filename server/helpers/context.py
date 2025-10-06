from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Optional

__all__ = [
  "bind_request_id",
  "get_request_id",
  "request_id_context",
  "reset_request_id",
]

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
  return _request_id_ctx.get()


def bind_request_id(request_id: Optional[str]) -> Token[Optional[str]]:
  return _request_id_ctx.set(request_id)


def reset_request_id(token: Token[Optional[str]]) -> None:
  _request_id_ctx.reset(token)


@contextmanager
def request_id_context(request_id: Optional[str]) -> Iterator[None]:
  token = bind_request_id(request_id)
  try:
    yield
  finally:
    reset_request_id(token)
