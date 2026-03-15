"""MSSQL implementations for finance journal lines query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one, transaction

__all__ = ["create_line_v1", "create_lines_batch_v1", "delete_by_journal_v1", "list_by_journal_v1"]


async def list_by_journal_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      line.recid,
      line.journals_recid,
      line.element_line_number,
      line.accounts_guid,
      line.element_debit,
      line.element_credit,
      line.element_description,
      line.element_created_on,
      line.element_modified_on,
      COALESCE(
        (
          SELECT
            JSON_QUERY(
              CONCAT(
                '[',
                STRING_AGG(CAST(link.dimensions_recid AS NVARCHAR(20)), ',') WITHIN GROUP (ORDER BY link.dimensions_recid),
                ']'
              )
            )
          FROM finance_journal_line_dimensions AS link
          WHERE link.lines_recid = line.recid
        ),
        JSON_QUERY('[]')
      ) AS dimension_recids
    FROM finance_journal_lines AS line
    WHERE line.journals_recid = ?
    ORDER BY line.element_line_number
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["journals_recid"],))


async def create_line_v1(args: Mapping[str, Any]) -> DBResponse:
  async with transaction() as cur:
    await cur.execute(
      """
      INSERT INTO finance_journal_lines (
        journals_recid,
        element_line_number,
        accounts_guid,
        element_debit,
        element_credit,
        element_description,
        element_created_on,
        element_modified_on
      ) VALUES (
        ?,
        ?,
        TRY_CAST(? AS UNIQUEIDENTIFIER),
        CAST(? AS DECIMAL(19,5)),
        CAST(? AS DECIMAL(19,5)),
        ?,
        SYSUTCDATETIME(),
        SYSUTCDATETIME()
      );
      """,
      (
        args["journals_recid"],
        args["line_number"],
        args["accounts_guid"],
        args["debit"],
        args["credit"],
        args.get("description"),
      ),
    )
    await cur.execute("SELECT CAST(SCOPE_IDENTITY() AS BIGINT) AS recid;")
    identity_row = await cur.fetchone()
    line_recid = int(identity_row[0])

    for dimension_recid in args.get("dimension_recids", []):
      await cur.execute(
        """
        INSERT INTO finance_journal_line_dimensions (lines_recid, dimensions_recid)
        VALUES (?, ?);
        """,
        (line_recid, dimension_recid),
      )

  return await run_json_one(
    """
    SELECT
      line.recid,
      line.journals_recid,
      line.element_line_number,
      line.accounts_guid,
      line.element_debit,
      line.element_credit,
      line.element_description,
      line.element_created_on,
      line.element_modified_on,
      COALESCE(
        (
          SELECT
            JSON_QUERY(
              CONCAT(
                '[',
                STRING_AGG(CAST(link.dimensions_recid AS NVARCHAR(20)), ',') WITHIN GROUP (ORDER BY link.dimensions_recid),
                ']'
              )
            )
          FROM finance_journal_line_dimensions AS link
          WHERE link.lines_recid = line.recid
        ),
        JSON_QUERY('[]')
      ) AS dimension_recids
    FROM finance_journal_lines AS line
    WHERE line.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
    """,
    (line_recid,),
  )


async def create_lines_batch_v1(args: Mapping[str, Any]) -> DBResponse:
  created_count = 0
  for line in args.get("lines", []):
    line_payload = dict(line)
    line_payload["journals_recid"] = args["journals_recid"]
    await create_line_v1(line_payload)
    created_count += 1

  return DBResponse(payload={"created": created_count}, rowcount=created_count)


async def delete_by_journal_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    DELETE FROM finance_journal_line_dimensions
    WHERE lines_recid IN (
      SELECT recid FROM finance_journal_lines WHERE journals_recid = ?
    );

    DELETE FROM finance_journal_lines
    WHERE journals_recid = ?;
  """
  return await run_exec(sql, (args["journals_recid"], args["journals_recid"]))
