from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess

from scriptlib import apply_schema, bump_version, connect, dump_data, dump_schema, select_environment


logger = logging.getLogger(__name__)


def _commit_and_tag(version: str, schema_file: str) -> None:
  logger.debug('Staging schema file %s for version %s', schema_file, version)
  subprocess.check_call(['git', 'add', schema_file])
  logger.debug('Creating commit for version %s', version)
  subprocess.check_call(['git', 'commit', '-m', f'Exported DB schema for {version}'])
  logger.debug('Tagging commit with %s', version)
  subprocess.check_call(['git', 'tag', version])

  current_branch = subprocess.check_output(
    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
    text=True,
  ).strip()
  logger.debug('Pushing branch %s to origin', current_branch)
  subprocess.check_call(['git', 'push', 'origin', current_branch])
  logger.debug('Pushing tags to origin')
  subprocess.check_call(['git', 'push', 'origin', '--tags'])


async def _update_config(conn, key: str, value: str):
  async with conn.cursor() as cur:
    logger.debug('Updating system_config key %s to %s', key, value)
    await cur.execute(
      "UPDATE system_config SET element_value=? WHERE element_key=?",
      (value, key),
    )
    if cur.rowcount == 0:
      logger.debug('system_config key %s missing; inserting new value %s', key, value)
      await cur.execute(
        "INSERT INTO system_config(element_key, element_value) VALUES(?, ?)",
        (key, value),
      )

HELP_TEXT = """\
Available commands:
  help                               Show this help message
  exit, quit                         Exit the console
  reconnect <db>                     Connect to a different database
  index all                          Reindex the current database
  schema dump [name]                 Dump DB schema to <name>_YYYYMMDD.sql
  schema apply <file>                Execute schema SQL on the database
  dump data [name]                   Dump DB schema and rows to <name>_YYYYMMDD.json
  update version major               Increment the major version
  update version minor               Increment the minor version
  update version patch               Increment the patch version
"""

async def interactive_console(conn):
  print("Type 'help' for commands. Type 'exit' to quit.")
  while True:
    try:
      raw = input('SQL> ')
    except EOFError:
      print()
      break
    except KeyboardInterrupt:
      print()
      continue
    raw = raw.strip()
    if not raw:
      continue
    cmd = raw.split()
    logger.debug('Received command: %s', cmd)
    match cmd:
      case ['quit'] | ['exit']:
        break
      case ['help']:
        print(HELP_TEXT)
      case ['reconnect', dbname]:
        try:
          await conn.close()
          logger.debug('Reconnecting to database %s', dbname)
          conn = await connect(dbname)
        except Exception as e:
          print(f'Error reconnecting: {e}')
      case ['index', 'all']:
        try:
          async with conn.cursor() as cur:
            await cur.execute("EXEC sp_MSforeachtable 'ALTER INDEX ALL ON ? REBUILD'")
          print('Reindex complete.')
        except Exception as e:
          print(f'Error: {e}')
      case ['schema', 'dump']:
        logger.debug('Dumping schema with default prefix')
        await dump_schema(conn)
      case ['schema', 'dump', name]:
        logger.debug('Dumping schema with prefix %s', name)
        await dump_schema(conn, name)
      case ['schema', 'apply', file]:
        try:
          logger.debug('Applying schema file %s', file)
          await apply_schema(conn, file)
        except Exception as e:
          print(f'Error applying schema: {e}')
      case ['dump', 'data']:
        logger.debug('Dumping data with default prefix')
        await dump_data(conn)
      case ['dump', 'data', name]:
        logger.debug('Dumping data with prefix %s', name)
        await dump_data(conn, name)
      case ['update', 'version', part] if part in {'major', 'minor', 'patch'}:
        cur_ver = None
        config_updated = False
        try:
          async with conn.cursor() as cur:
            await cur.execute("SELECT element_value FROM system_config WHERE element_key='Version'")
            row = await cur.fetchone()
          if not row:
            print('Version entry not found in system_config table')
            continue
          cur_ver = row[0]
          new_ver = bump_version(cur_ver, part)
          logger.debug('Computed new version %s from %s using part %s', new_ver, cur_ver, part)
          await _update_config(conn, 'Version', new_ver)
          config_updated = True
          print(f'Updated Version: {cur_ver} -> {new_ver}')
          logger.debug('Dumping schema for version %s', new_ver)
          schema_file = await dump_schema(conn, new_ver)
          _commit_and_tag(new_ver, schema_file)
        except Exception as exc:
          print(f'Error updating version: {exc}')
          if config_updated and cur_ver is not None:
            try:
              logger.debug('Attempting to roll back Version to %s', cur_ver)
              await _update_config(conn, 'Version', cur_ver)
              print(f'Reverted Version to {cur_ver}')
            except Exception as rollback_exc:
              print(f'Failed to roll back Version update: {rollback_exc}')
      case _:
        try:
          async with conn.cursor() as cur:
            logger.debug('Executing raw SQL: %s', raw)
            await cur.execute(raw)
            try:
              rows = await cur.fetchall()
              cols = [d[0] for d in cur.description]
              for row in rows:
                print(dict(zip(cols, row)))
            except Exception:
              print(cur.rowcount)
        except Exception as e2:
          print(f'Error: {e2}')

def parse_args():
  parser = argparse.ArgumentParser(description='Interactive MSSQL CLI tool')
  parser.add_argument(
    '-e',
    '--env',
    choices=['prod', 'test'],
    default='test',
    help='Select environment configuration (default: test)',
  )
  return parser.parse_args()


async def run_cli():
  conn = await connect()
  try:
    logger.debug('Starting interactive console session')
    await interactive_console(conn)
  finally:
    logger.debug('Closing database connection')
    await conn.close()


def main():
  args = parse_args()
  logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
  logger.debug('Initializing CLI with args: %s', args)
  select_environment(args.env)
  print(f"Using {args.env} environment configuration")
  logger.debug('Launching CLI event loop')
  asyncio.run(run_cli())


if __name__ == '__main__':
  main()
