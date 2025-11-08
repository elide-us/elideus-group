"""Helper utilities for query registry dispatch."""

from __future__ import annotations

from typing import Sequence

from queryregistry.models import DBRequest


def parse_query_operation(op: str) -> tuple[str, tuple[str, ...]]:
  parts = op.split(":")
  if len(parts) < 3 or parts[0] != "db":
    raise ValueError(f"Invalid query operation: {op}")
  domain = parts[1]
  remainder = tuple(parts[2:])
  if not domain:
    raise ValueError(f"Missing query domain in operation: {op}")
  return domain, remainder


def parse_query_request(request: DBRequest) -> tuple[str, Sequence[str]]:
  return parse_query_operation(request.op)
