"""Assistant persona queries for MSSQL."""

from __future__ import annotations

from typing import Any

from server.modules.providers import DBResult, DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation, exec_op, exec_query

__all__ = [
  "delete_persona_v1",
  "get_by_name_v1",
  "list_personas_v1",
  "upsert_persona_v1",
]


def get_by_name_v1(args: dict[str, Any]) -> Operation:
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
    FROM vw_personas vp
    JOIN assistant_personas ap ON ap.element_name = vp.persona_name
    WHERE vp.persona_name = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return Operation(DbRunMode.JSON_ONE, sql, (name,))


def list_personas_v1(_: dict[str, Any]) -> Operation:
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
    FROM vw_personas vp
    JOIN assistant_personas ap ON ap.element_name = vp.persona_name
    ORDER BY vp.persona_name
    FOR JSON PATH;
  """
  return Operation(DbRunMode.JSON_MANY, sql, ())


async def upsert_persona_v1(args: dict[str, Any]) -> DBResult:
  recid = args.get("recid")
  name = args["name"]
  prompt = args["prompt"]
  tokens = int(args["tokens"])
  models_recid = int(args["models_recid"])
  if recid is not None:
    rc = await exec_query(exec_op(
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
    ))
    if rc.rowcount:
      return rc
  rc = await exec_query(exec_op(
    """
      UPDATE assistant_personas
      SET element_prompt = ?,
          element_tokens = ?,
          models_recid = ?,
          element_modified_on = SYSUTCDATETIME()
      WHERE element_name = ?;
    """,
    (prompt, tokens, models_recid, name),
  ))
  if rc.rowcount:
    return rc
  return await exec_query(exec_op(
    """
      INSERT INTO assistant_personas (
        element_name,
        element_prompt,
        element_tokens,
        models_recid
      ) VALUES (?, ?, ?, ?);
    """,
    (name, prompt, tokens, models_recid),
  ))


def delete_persona_v1(args: dict[str, Any]) -> Operation:
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
  return Operation(DbRunMode.EXEC, sql, params)
