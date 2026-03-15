"""Storage reindex batch job.

Callable path for batch job registration: server.jobs.storage_reindex.run
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI


async def run(app: FastAPI, params: dict[str, Any]) -> dict[str, Any]:
  """Execute a full storage reindex.

  Params (all optional):
      user_guid: str — if provided, reindex only this user's files.

  Returns dict with reindex summary.
  """
  storage = getattr(app.state, "storage", None)
  if storage is None:
    raise RuntimeError("StorageModule is not available")
  await storage.on_ready()

  user_guid = params.get("user_guid")
  await storage.reindex(user_guid=user_guid)

  return {
    "status": "completed",
    "user_guid": user_guid,
  }
