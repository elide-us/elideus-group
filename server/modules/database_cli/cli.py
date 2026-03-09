"""Interactive CLI for database helpers."""

from __future__ import annotations

import asyncio
import logging
import os

from .. import database_cli_module
from . import mssql_cli


DEFAULT_DATABASE_PLACEHOLDER = "database"


HELP_TEXT = """\
Available commands:
  help
  connect <database>
  reconnect [database]
  list tables
  schema dump [name]
  schema apply <file>
  dump data [name]
  update version major|minor|patch
  index all
  exit, quit

Any unrecognized command is executed as raw SQL.
"""


def _get_dsn() -> str:
  dsn = os.environ.get("AZURE_SQL_CONNECTION_STRING")
  if not dsn:
    logging.error("[DatabaseCli] AZURE_SQL_CONNECTION_STRING not set")
    raise RuntimeError("AZURE_SQL_CONNECTION_STRING not set")
  return dsn


def _prompt(dbname: str | None) -> str:
  label = dbname or DEFAULT_DATABASE_PLACEHOLDER
  return f"{label}> "


def _print_help():
  print(HELP_TEXT)


def run_repl():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  conn = None
  dbname: str | None = None
  try:
    while True:
      try:
        raw = input(_prompt(dbname))
      except (EOFError, KeyboardInterrupt):
        print()
        break
      raw = raw.strip()
      if not raw:
        continue
      parts = raw.split()

      if parts == ["help"]:
        _print_help()
        continue
      if parts in (["exit"], ["quit"]):
        break

      if parts[0].lower() == "connect":
        target_db = parts[1] if len(parts) > 1 else None
        try:
          conn = loop.run_until_complete(mssql_cli.connect(dsn=_get_dsn(), dbname=target_db))
          dbname = target_db
        except Exception:
          logging.exception("[DatabaseCli] Failed to connect")
        continue

      if parts[0].lower() == "reconnect":
        target_db = parts[1] if len(parts) > 1 else dbname
        if not target_db:
          print("No database selected. Use: connect <database>.")
          continue
        try:
          conn = loop.run_until_complete(
            mssql_cli.reconnect(conn, dsn=_get_dsn(), dbname=target_db)
          )
          dbname = target_db
        except Exception:
          logging.exception("[DatabaseCli] Failed to reconnect")
        continue

      if parts[:2] == ["list", "tables"]:
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        try:
          tables = loop.run_until_complete(mssql_cli.list_tables(conn))
          print("\n".join(tables) if tables else "No tables found.")
        except Exception:
          logging.exception("[DatabaseCli] Failed to list tables")
        continue

      if parts[:2] == ["schema", "dump"]:
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        prefix = parts[2] if len(parts) > 2 else "schema"
        try:
          loop.run_until_complete(database_cli_module.dump_schema_from_registry(conn, prefix))
        except Exception:
          logging.exception("[DatabaseCli] Failed to dump schema")
        continue

      if parts[:2] == ["schema", "apply"] and len(parts) > 2:
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        try:
          loop.run_until_complete(database_cli_module.apply_schema(conn, parts[2]))
        except Exception:
          logging.exception("[DatabaseCli] Failed to apply schema")
        continue

      if parts[:2] == ["dump", "data"]:
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        prefix = parts[2] if len(parts) > 2 else "dump_data"
        try:
          loop.run_until_complete(database_cli_module.dump_data(conn, prefix))
        except Exception:
          logging.exception("[DatabaseCli] Failed to dump data")
        continue

      if parts[:2] == ["index", "all"]:
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        try:
          loop.run_until_complete(database_cli_module.rebuild_indexes(conn))
        except Exception:
          logging.exception("[DatabaseCli] Failed to rebuild indexes")
        continue

      if len(parts) == 3 and parts[:2] == ["update", "version"] and parts[2] in {
        "major",
        "minor",
        "patch",
      }:
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        try:
          new_version = loop.run_until_complete(database_cli_module.update_version(conn, parts[2]))
          schema_file = loop.run_until_complete(
            database_cli_module.dump_schema_from_registry(conn, new_version)
          )
          database_cli_module.commit_and_tag(new_version, schema_file)
        except Exception:
          logging.exception("[DatabaseCli] Failed to update version")
        continue

      if not conn:
        print("Not connected. Use: connect <database>.")
        continue

      try:
        async def _run_sql():
          async with conn.cursor() as cur:
            await cur.execute(raw)
            try:
              rows = await cur.fetchall()
              cols = [desc[0] for desc in cur.description]
              for row in rows:
                print(dict(zip(cols, row)))
            except Exception:
              print(cur.rowcount)

        loop.run_until_complete(_run_sql())
      except Exception:
        logging.exception("[DatabaseCli] Raw SQL failed")
  finally:
    if conn:
      try:
        loop.run_until_complete(conn.close())
      except Exception:
        logging.exception("[DatabaseCli] Failed to close connection")
      else:
        logging.info("[DatabaseCli] Connection closed")
    loop.close()
