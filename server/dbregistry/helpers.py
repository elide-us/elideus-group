"""Helper utilities for database registry dispatch."""

from __future__ import annotations

from typing import Sequence

from server.registry.models import DBRequest


def parse_db_operation(op: str) -> tuple[str, tuple[str, ...]]:
  parts = op.split(":")
  if len(parts) < 3 or parts[0] != "db":
    raise ValueError(f"Invalid database operation: {op}")
  domain = parts[1]
  remainder = tuple(parts[2:])
  if not domain:
    raise ValueError(f"Missing database domain in operation: {op}")
  return domain, remainder


def parse_db_request(request: DBRequest) -> tuple[str, Sequence[str]]:
  return parse_db_operation(request.op)
