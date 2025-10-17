"""MSSQL helpers for auth provider operations."""

from __future__ import annotations

from typing import Any

from server.registry.providers.mssql import run_exec
from server.registry.types import DBResponse

__all__ = ["unlink_last_provider_v1"]


async def unlink_last_provider_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  provider = args["provider"]
  sql = "EXEC auth_unlink_last_provider @guid=?, @provider=?;"
  return await run_exec(sql, (guid, provider))
