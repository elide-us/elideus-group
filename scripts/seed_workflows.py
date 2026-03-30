"""Seed system workflow definitions."""

from __future__ import annotations

import argparse
import os
import sys
import uuid

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.common import REPO_ROOT, RPC_REFLECTION_NAMESPACE

load_dotenv(os.path.join(REPO_ROOT, ".env"))


def reflection_function_guid(natural_key: str) -> str:
  return str(uuid.uuid5(RPC_REFLECTION_NAMESPACE, natural_key))


WORKFLOW_NAME = "persona_conversation"
WORKFLOW_DESCRIPTION = "Persona-driven conversational response pipeline"
WORKFLOW_VERSION = 1
WORKFLOW_STATUS = 1

WORKFLOW_STEPS = [
  (1, "resolve_persona", "pipe", "harmless", "server.workflows.steps.conversation.ResolvePersonaStep", 0),
  (2, "gather_stored_context", "pipe", "harmless", "server.workflows.steps.conversation.GatherStoredContextStep", 0),
  (3, "assemble_prompt", "pipe", "harmless", "server.workflows.steps.conversation.AssemblePromptStep", 0),
  (4, "generate_response", "pipe", "harmless", "server.workflows.steps.conversation.GenerateResponseStep", 0),
  (5, "log_conversation", "stack", "reversible", "server.workflows.steps.conversation.LogConversationStep", 0),
  (6, "deliver_response", "pipe", "harmless", "server.workflows.steps.conversation.DeliverResponseStep", 0),
]

BILLING_IMPORT_NAME = "billing_import"
BILLING_IMPORT_DESCRIPTION = "Promote approved billing staging imports into posted journals."
BILLING_IMPORT_VERSION = 1
BILLING_IMPORT_STATUS = 1

BILLING_IMPORT_STEPS = [
  (1, "validate_import", "pipe", "harmless", "server.workflows.steps.billing_import.ValidateImportStep", 0),
  (2, "classify_costs", "pipe", "harmless", "server.workflows.steps.billing_import.ClassifyCostsStep", 0),
  (3, "create_journal", "pipe", "irreversible", "server.workflows.steps.billing_import.CreateJournalStep", 0),
  (4, "mark_promoted", "pipe", "irreversible", "server.workflows.steps.billing_import.MarkPromotedStep", 0),
]


def connect() -> pyodbc.Connection:
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING_DEV") or os.environ.get("AZURE_SQL_CONNECTION_STRING")
  if not dsn:
    raise RuntimeError("Missing AZURE_SQL_CONNECTION_STRING_DEV/AZURE_SQL_CONNECTION_STRING in environment")
  return pyodbc.connect(dsn, autocommit=True)


def seed_workflow(
  *,
  force: bool,
  name: str,
  description: str,
  version: int,
  status: int,
  steps: list[tuple[int, str, str, str, str, int]],
) -> None:
  conn = connect()
  try:
    cursor = conn.cursor()
    cursor.execute("SET XACT_ABORT ON;")
    cursor.execute("BEGIN TRANSACTION;")

    existing_rows = cursor.execute(
      "SELECT element_guid FROM system_workflows WHERE element_name = ?;",
      [name],
    ).fetchall()

    if existing_rows and not force:
      cursor.execute("ROLLBACK TRANSACTION;")
      print(f"Workflow '{name}' already exists; skipping (use --force to reseed).")
      return

    if existing_rows and force:
      cursor.execute(
        """
        DELETE s
        FROM system_workflow_steps s
        INNER JOIN system_workflows w ON w.element_guid = s.workflows_guid
        WHERE w.element_name = ?;
        """,
        [name],
      )
      cursor.execute("DELETE FROM system_workflows WHERE element_name = ?;", [name])

    workflow_guid = cursor.execute(
      """
      INSERT INTO system_workflows (
        element_name,
        element_description,
        element_version,
        element_status,
        element_created_on,
        element_modified_on
      )
      OUTPUT inserted.element_guid
      VALUES (?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME());
      """,
      [name, description, version, status],
    ).fetchval()

    for sequence, step_name, step_type, disposition, class_path, is_optional in steps:
      cursor.execute(
        """
        INSERT INTO system_workflow_steps (
          workflows_guid,
          element_sequence,
          element_name,
          element_step_type,
          element_disposition,
          element_class_path,
          element_is_optional
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        [workflow_guid, sequence, step_name, step_type, disposition, class_path, is_optional],
      )

    cursor.execute("COMMIT TRANSACTION;")
    print(f"Workflow '{name}' GUID: {workflow_guid}")
    print(f"Workflow '{name}' step count: {len(steps)}")
  except Exception:
    try:
      cursor.execute("ROLLBACK TRANSACTION;")
    except Exception:
      pass
    raise
  finally:
    conn.close()


def main() -> None:
  parser = argparse.ArgumentParser(description="Seed system_workflows/system_workflow_steps")
  parser.add_argument("--force", action="store_true", help="Reseed by deleting existing workflow rows")
  args = parser.parse_args()

  seed_workflow(
    force=args.force,
    name=WORKFLOW_NAME,
    description=WORKFLOW_DESCRIPTION,
    version=WORKFLOW_VERSION,
    status=WORKFLOW_STATUS,
    steps=WORKFLOW_STEPS,
  )
  seed_workflow(
    force=args.force,
    name=BILLING_IMPORT_NAME,
    description=BILLING_IMPORT_DESCRIPTION,
    version=BILLING_IMPORT_VERSION,
    status=BILLING_IMPORT_STATUS,
    steps=BILLING_IMPORT_STEPS,
  )


if __name__ == "__main__":
  main()
