"""Interactive CLI for database helpers."""

from __future__ import annotations

import asyncio
import logging
import os

from . import mssql_cli


DEFAULT_DATABASE_PLACEHOLDER = "database"


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
  print("Available commands:")
  print("  help")
  print("  connect <database>")
  print("  reconnect [database]")
  print("  list tables")


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
      command = parts[0].lower()
      if command == "help":
        _print_help()
        continue
      if command == "connect":
        target_db = parts[1] if len(parts) > 1 else None
        try:
          conn = loop.run_until_complete(
            mssql_cli.connect(dsn=_get_dsn(), dbname=target_db)
          )
          dbname = target_db
        except Exception:
          logging.exception("[DatabaseCli] Failed to connect")
        continue
      if command == "reconnect":
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
      if command == "list" and len(parts) > 1 and parts[1].lower() == "tables":
        if not conn:
          print("Not connected. Use: connect <database>.")
          continue
        try:
          tables = loop.run_until_complete(mssql_cli.list_tables(conn))
          if tables:
            print("\n".join(tables))
          else:
            print("No tables found.")
        except Exception:
          logging.exception("[DatabaseCli] Failed to list tables")
        continue
      print(f"Unknown command: {raw}. Type 'help' for available commands.")
  finally:
    if conn:
      try:
        loop.run_until_complete(conn.close())
      except Exception:
        logging.exception("[DatabaseCli] Failed to close connection")
      else:
        logging.info("[DatabaseCli] Connection closed")
    loop.close()
