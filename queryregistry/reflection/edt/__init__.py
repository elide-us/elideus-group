"""Reflection EDT query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

__all__ = ["list_edt_mappings_request"]


def list_edt_mappings_request() -> DBRequest:
  return DBRequest(op="db:reflection:edt:list:1", payload={})
