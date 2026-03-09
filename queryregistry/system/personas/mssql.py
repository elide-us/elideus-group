"""MSSQL implementations for system personas query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from queryregistry.models import DBResponse

__all__ = [
  "delete_persona_v1",
  "get_by_name_v1",
  "list_personas_v1",
  "upsert_persona_v1",
]


async def get_by_name_v1(args: Mapping[str, Any]) -> DBResponse:
  name = args["name"]
  sql = """
    SELECT
      ap.recid,
      ap.models_recid,
      vp.persona_name AS persona_name,
      vp.persona_name AS name,
      vp.system_role_prompt AS system_role_prompt,
      vp.system_role_prompt AS prompt,
      vp.system_role_prompt AS element_prompt,
      vp.token_allowance AS token_allowance,
      vp.token_allowance AS tokens,
      vp.token_allowance AS element_tokens,
      vp.model_name AS model_name,
      vp.model_name AS model,
      vp.model_name AS element_model,
      vp.element_created_on,
      vp.element_modified_on
    FROM vw_content_personas vp
    JOIN assistant_personas ap ON ap.element_name = vp.persona_name
    WHERE vp.persona_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (name,))


async def list_personas_v1(_: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      ap.recid,
      ap.models_recid,
      vp.persona_name AS persona_name,
      vp.persona_name AS name,
      vp.system_role_prompt AS system_role_prompt,
      vp.system_role_prompt AS prompt,
      vp.system_role_prompt AS element_prompt,
      vp.token_allowance AS token_allowance,
      vp.token_allowance AS tokens,
      vp.token_allowance AS element_tokens,
      vp.model_name AS model_name,
      vp.model_name AS model,
      vp.model_name AS element_model,
      vp.element_created_on,
      vp.element_modified_on
    FROM vw_content_personas vp
    JOIN assistant_personas ap ON ap.element_name = vp.persona_name
    ORDER BY vp.persona_name
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def upsert_persona_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args.get("recid")
  name = args["name"]
  prompt = args["prompt"]
  tokens = int(args["tokens"])
  models_recid = int(args["models_recid"])
  if recid is not None:
    rc = await run_exec(
      """
        UPDATE assistant_personas
        SET element_name = ?,
            element_prompt = ?,
            element_tokens = ?,
            models_recid = ?,
            element_modified_on = SYSUTCDATETIME()
        WHERE recid = ?;
      """,
      (name, prompt, tokens, models_recid, recid),
    )
    if rc.rowcount:
      return rc
  rc = await run_exec(
    """
      UPDATE assistant_personas
      SET element_prompt = ?,
          element_tokens = ?,
          models_recid = ?,
          element_modified_on = SYSUTCDATETIME()
      WHERE element_name = ?;
    """,
    (prompt, tokens, models_recid, name),
  )
  if rc.rowcount:
    return rc
  return await run_exec(
    """
      INSERT INTO assistant_personas (
        element_name,
        element_prompt,
        element_tokens,
        models_recid
      ) VALUES (?, ?, ?, ?);
    """,
    (name, prompt, tokens, models_recid),
  )


async def delete_persona_v1(args: Mapping[str, Any]) -> DBResponse:
  recid = args.get("recid")
  name = args.get("name")
  if recid is not None:
    sql = "DELETE FROM assistant_personas WHERE recid = ?;"
    params = (recid,)
  elif name is not None:
    sql = "DELETE FROM assistant_personas WHERE element_name = ?;"
    params = (name,)
  else:
    raise ValueError("Missing identifier for persona delete")
  return await run_exec(sql, params)
