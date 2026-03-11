"""Interactive CLI for database helpers."""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI

from .. import database_cli_module
from ..db_module import DbModule
from ..env_module import EnvModule
from . import mssql_cli



HELP_TEXT = """\
Available commands:
  help
  reconnect
  list tables
  schema dump [name]
  schema apply <file>
  dump data [name]
  seed dump [name]
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


def _prompt() -> str:
  return "cli> "


def _print_help():
  print(HELP_TEXT)


async def _bootstrap() -> tuple[FastAPI, database_cli_module.DatabaseCliModule]:
  app = FastAPI()

  env_mod = EnvModule(app)
  setattr(app.state, "env", env_mod)
  await env_mod.startup()

  db_mod = DbModule(app)
  setattr(app.state, "db", db_mod)
  await db_mod.startup()

  cli_mod = database_cli_module.DatabaseCliModule(app)
  setattr(app.state, "database_cli", cli_mod)
  await cli_mod.startup()

  return app, cli_mod


async def _shutdown(app: FastAPI):
  cli_mod = getattr(app.state, "database_cli", None)
  db_mod = getattr(app.state, "db", None)
  env_mod = getattr(app.state, "env", None)

  if cli_mod:
    await cli_mod.shutdown()
    setattr(app.state, "database_cli", None)
  if db_mod:
    await db_mod.shutdown()
    setattr(app.state, "db", None)
  if env_mod:
    await env_mod.shutdown()
    setattr(app.state, "env", None)


def run_repl():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  raw_conn = None
  app = None
  cli_mod = None
  try:
    try:
      app, cli_mod = loop.run_until_complete(_bootstrap())
    except Exception as e:
      print(f"Error: {e}")
      logging.exception("[DatabaseCli] Failed during bootstrap")
      return
    while True:
      try:
        raw = input(_prompt())
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

      if parts == ["reconnect"]:
        try:
          if app:
            loop.run_until_complete(_shutdown(app))
          if raw_conn:
            try:
              loop.run_until_complete(raw_conn.close())
            except Exception:
              pass
            raw_conn = None
          app, cli_mod = loop.run_until_complete(_bootstrap())
          print("Reconnected.")
        except Exception as e:
          print(f"Reconnect failed: {e}")
          logging.exception("[DatabaseCli] Reconnect failed")
        continue

      if parts[:2] == ["list", "tables"]:
        try:
          tables = loop.run_until_complete(cli_mod.list_tables())
          print("\n".join(tables) if tables else "No tables found.")
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to list tables")
        continue

      if parts[:2] == ["schema", "dump"]:
        prefix = parts[2] if len(parts) > 2 else "schema"
        try:
          loop.run_until_complete(cli_mod.dump_schema_from_registry(prefix))
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to dump schema")
        continue

      if parts[:2] == ["schema", "apply"] and len(parts) > 2:
        try:
          loop.run_until_complete(cli_mod.apply_schema(parts[2]))
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to apply schema")
        continue

      if parts[:2] == ["dump", "data"]:
        prefix = parts[2] if len(parts) > 2 else "dump_data"
        try:
          loop.run_until_complete(cli_mod.dump_data(prefix))
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to dump data")
        continue


      if parts[:2] == ["seed", "dump"]:
        prefix = parts[2] if len(parts) > 2 else "seed"
        try:
          loop.run_until_complete(cli_mod.dump_seed_from_registry(prefix))
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to dump seed")
        continue
      if parts[:2] == ["index", "all"]:
        try:
          loop.run_until_complete(cli_mod.rebuild_indexes())
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to rebuild indexes")
        continue

      if len(parts) == 3 and parts[:2] == ["update", "version"] and parts[2] in {
        "major",
        "minor",
        "patch",
      }:
        try:
          new_version = loop.run_until_complete(cli_mod.update_version(parts[2]))
          schema_file = loop.run_until_complete(cli_mod.dump_schema_from_registry(new_version))
          seed_file = loop.run_until_complete(cli_mod.dump_seed_from_registry(new_version + "_seed"))
          cli_mod.commit_and_tag(new_version, [schema_file, seed_file])
        except Exception as e:
          print(f"Error: {e}")
          logging.exception("[DatabaseCli] Failed to update version")
        continue

      try:
        async def _run_sql():
          nonlocal raw_conn
          if not raw_conn:
            raw_conn = await mssql_cli.connect(dsn=_get_dsn())
          async with raw_conn.cursor() as cur:
            await cur.execute(raw)
            try:
              rows = await cur.fetchall()
              cols = [desc[0] for desc in cur.description]
              for row in rows:
                print(dict(zip(cols, row)))
            except Exception:
              print(cur.rowcount)

        loop.run_until_complete(_run_sql())
      except Exception as e:
        print(f"Error: {e}")
        logging.exception("[DatabaseCli] Raw SQL failed")
  finally:
    if raw_conn:
      try:
        loop.run_until_complete(raw_conn.close())
      except Exception as e:
        print(f"Error: {e}")
        logging.exception("[DatabaseCli] Failed to close connection")
      else:
        logging.info("[DatabaseCli] Connection closed")
    if app:
      try:
        loop.run_until_complete(_shutdown(app))
      except Exception as e:
        print(f"Error: {e}")
        logging.exception("[DatabaseCli] Failed to shutdown modules")
    loop.close()
