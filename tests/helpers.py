"""Shared helpers for tests interacting with database request mocks."""

from __future__ import annotations

from collections.abc import Mapping

from server.registry.types import DBRequest


def call_op(call):
  """Return the operation name for a recorded database call."""
  op, _ = call
  return op.op if isinstance(op, DBRequest) else op


def call_payload(call):
  """Return a dictionary payload for a recorded database call."""
  op, payload = call
  if isinstance(op, DBRequest):
    payload = op.payload
  if payload is None:
    return {}
  if hasattr(payload, "model_dump"):
    return payload.model_dump()
  if isinstance(payload, Mapping):
    return dict(payload)
  return payload


def normalize_call(call):
  """Return the call as an (op, payload) tuple with primitives."""
  return call_op(call), call_payload(call)
