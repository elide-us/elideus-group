"""Seed system_workflow_actions for callable workflows."""

from __future__ import annotations

import argparse
import os
import sys

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import REPO_ROOT

load_dotenv(os.path.join(REPO_ROOT, ".env"))

STORAGE_WORKFLOW_GUID = "C1D2E3F4-A5B6-7890-CDEF-123456789010"
STALL_WORKFLOW_GUID = "D1E2F3A4-B5C6-7890-DEFA-123456789020"


def connect() -> pyodbc.Connection:
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING_DEV") or os.environ.get("AZURE_SQL_CONNECTION_STRING")
  if not dsn:
    raise RuntimeError("Missing AZURE_SQL_CONNECTION_STRING_DEV/AZURE_SQL_CONNECTION_STRING in environment")
  return pyodbc.connect(dsn, autocommit=True)


def get_function_guid(cursor: pyodbc.Cursor, subdomain: str, names: list[str]) -> str:
  placeholders = ", ".join("?" for _ in names)
  row = cursor.execute(
    f"""
    SELECT TOP 1 f.element_guid
    FROM reflection_rpc_functions f
    INNER JOIN reflection_rpc_subdomains s ON s.element_guid = f.subdomains_guid
    WHERE s.element_name = ?
      AND f.element_name IN ({placeholders})
      AND f.element_status = 1
    ORDER BY CASE f.element_name
      {" ".join([f"WHEN ? THEN {i}" for i, _ in enumerate(names, 1)])}
      ELSE 999 END;
    """,
    [subdomain, *names, *names],
  ).fetchone()
  if not row:
    raise RuntimeError(f"Could not find function in subdomain '{subdomain}' with names {names}")
  return str(row[0])


def seed_workflow_actions(force: bool) -> None:
  conn = connect()
  try:
    cursor = conn.cursor()
    cursor.execute("SET XACT_ABORT ON;")
    cursor.execute("BEGIN TRANSACTION;")

    if force:
      cursor.execute(
        """
        DELETE FROM system_workflow_actions
        WHERE workflows_guid IN (?, ?);
        """,
        [STORAGE_WORKFLOW_GUID, STALL_WORKFLOW_GUID],
      )

    storage_function_guid = get_function_guid(cursor, "workflows.storage", ["reindex", "reindex_storage", "get_stats"])
    stall_function_guid = get_function_guid(cursor, "workflows", ["scan_stalls"])

    cursor.execute(
      """
      DELETE FROM system_workflow_actions
      WHERE workflows_guid IN (?, ?);
      """,
      [STORAGE_WORKFLOW_GUID, STALL_WORKFLOW_GUID],
    )

    cursor.execute(
      """
      INSERT INTO system_workflow_actions (
        workflows_guid,
        element_name,
        element_description,
        functions_guid,
        dispositions_recid,
        element_sequence,
        element_is_optional,
        element_is_active,
        element_created_on,
        element_modified_on
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME());
      """,
      [
        STORAGE_WORKFLOW_GUID,
        "reindex_storage",
        "Scan blob storage and sync users_storage_cache",
        storage_function_guid,
        3,
        1,
        0,
        1,
      ],
    )

    cursor.execute(
      """
      INSERT INTO system_workflow_actions (
        workflows_guid,
        element_name,
        element_description,
        functions_guid,
        dispositions_recid,
        element_sequence,
        element_is_optional,
        element_is_active,
        element_created_on,
        element_modified_on
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME());
      """,
      [
        STALL_WORKFLOW_GUID,
        "scan_stalled_runs",
        "Scan for runs exceeding stall threshold",
        stall_function_guid,
        3,
        1,
        0,
        1,
      ],
    )

    cursor.execute("COMMIT TRANSACTION;")
    print("Seeded system_workflow_actions for storage_reindex and stall_monitor.")
  except Exception:
    try:
      cursor.execute("ROLLBACK TRANSACTION;")
    except Exception:
      pass
    raise
  finally:
    conn.close()


def main() -> None:
  parser = argparse.ArgumentParser(description="Seed system_workflow_actions")
  parser.add_argument("--force", action="store_true", help="Delete and reseed workflow action rows")
  args = parser.parse_args()
  seed_workflow_actions(force=args.force)


if __name__ == "__main__":
  main()
