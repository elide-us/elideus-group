from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI

from server.modules import BaseModule
from server.modules.db_module import DbModule


class DiscordPersonasModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def list_models(self) -> List[Dict[str, Any]]:
    assert self.db
    res = await self.db.run("db:assistant:models:list:1", {})
    return list(res.rows or [])

  async def list_personas(self) -> List[Dict[str, Any]]:
    assert self.db
    res = await self.db.run("db:assistant:personas:list:1", {})
    personas: List[Dict[str, Any]] = []
    for row in res.rows or []:
      personas.append({
        "recid": row.get("recid"),
        "name": row.get("name", ""),
        "prompt": row.get("prompt", ""),
        "tokens": int(row.get("tokens", 0) or 0),
        "models_recid": (
          int(row.get("models_recid"))
          if row.get("models_recid") is not None
          else None
        ),
        "model": row.get("model"),
      })
    return personas

  async def upsert_persona(self, persona: Dict[str, Any]) -> None:
    assert self.db
    model_recid = persona.get("models_recid")
    if model_recid is None:
      raise ValueError("models_recid required")
    payload = {
      "recid": persona.get("recid"),
      "name": persona.get("name", ""),
      "prompt": persona.get("prompt", ""),
      "tokens": int(persona.get("tokens", 0) or 0),
      "models_recid": int(model_recid),
    }
    if not payload["name"]:
      raise ValueError("name required")
    await self.db.run("db:assistant:personas:upsert:1", payload)

  async def delete_persona(self, recid: int | None = None, name: str | None = None) -> None:
    assert self.db
    await self.db.run(
      "db:assistant:personas:delete:1",
      {"recid": recid, "name": name},
    )
