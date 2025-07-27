from __future__ import annotations
import asyncio
import subprocess
import dblib as db


import subprocess

def _commit_and_tag(version: str, schema_file: str) -> None:
    subprocess.check_call(f'git add {schema_file}', shell=True)
    subprocess.check_call(f'git commit -m "Exported DB schema for {version}"', shell=True)
    subprocess.check_call(f'git tag {version}', shell=True)

    current_branch = subprocess.check_output(
        "git rev-parse --abbrev-ref HEAD", shell=True, text=True
    ).strip()
    subprocess.check_call(f'git push origin {current_branch}', shell=True)
    subprocess.check_call('git push origin --tags', shell=True)


def _parse_version(ver: str) -> tuple[int, int, int, int]:
  ver = ver.lstrip('v')
  major, minor, patch, build = [int(v) for v in ver.split('.')]
  return major, minor, patch, build


async def _update_config(conn, key: str, value: str):
  res = await conn.execute(
    "UPDATE config SET value=$1 WHERE key=$2", value, key
  )
  if res.startswith('UPDATE 0'):
    await conn.execute(
      "INSERT INTO config(key, value) VALUES($1, $2)", key, value
    )

HELP_TEXT = """
Available commands:
  help                               Show this help message
  exit, quit                         Exit the console
  reconnect <db>                     Connect to a different database
  list tables                        List all tables
  list columns <table>               List columns of a table
  list indexes <table>               List indexes on a table
  index all                          Reindex the current database
  schema dump [name]                 Dump DB schema to <name>_YYYYMMDD.json
  schema apply <file>                Apply schema JSON to the database
  dump data [name]                   Dump DB schema and rows to <name>_YYYYMMDD.json
  update version major               Increment the major version
  update version minor               Increment the minor version
  update version patch               Increment the patch version
"""

async def interactive_console(conn):
  print("Type 'help' for commands. Type 'exit' to quit.")
  while True:
    raw = input('SQL> ').strip()
    if not raw:
      continue
    cmd = raw.split()
    match cmd:
      case ['quit'] | ['exit']:
        break
      case ['help']:
        print(HELP_TEXT)
      case ['reconnect', dbname]:
        try:
          await conn.close()
          conn = await db.connect(dbname)
        except Exception as e:
          print(f'Error reconnecting: {e}')
      case ['list', 'tables']:
        rows = await db.list_tables(conn)
        for r in rows:
          print(r['table_name'])
      case ['list', 'columns', table]:
        rows = await db.list_columns(conn, table)
        for r in rows:
          print(f"{r['column_name']} ({r['data_type']})")
      case ['list', 'indexes', table]:
        rows = await db.list_indexes(conn, table)
        for r in rows:
          print(f"{r['indexname']} ({r['indexdef']})")
      case ['index', 'all']:
        await conn.execute('REINDEX DATABASE current_database()')
        print('Reindex complete.')
      case ['schema', 'dump']:
        await db.dump_schema(conn)
      case ['schema', 'dump', name]:
        await db.dump_schema(conn, name)
      case ['schema', 'apply', file]:
        try:
          await db.apply_schema(conn, file)
        except Exception as e:
          print(f'Error applying schema: {e}')
      case ['dump', 'data']:
        await db.dump_data(conn)
      case ['dump', 'data', name]:
        await db.dump_data(conn, name)
      case ['update', 'version', part] if part in {'major', 'minor', 'patch'}:
        cur = await conn.fetchval("SELECT value FROM config WHERE key='Version'")
        if not cur:
          print('Version entry not found in config table')
          continue
        ma, mi, pa, bu = _parse_version(cur)
        match part:
          case 'major':
            ma += 1
            mi = 0
            pa = 0
            bu = 0
          case 'minor':
            mi += 1
            pa = 0
            bu = 0
          case 'patch':
            pa += 1
        new_ver = f"v{ma}.{mi}.{pa}.{bu}"
        await _update_config(conn, 'Version', new_ver)
        print(f'Updated Version: {cur} -> {new_ver}')
        schema_file = await db.dump_schema(conn, new_ver)
        _commit_and_tag(new_ver, schema_file)
      case _:
        try:
          rows = await conn.fetch(raw)
          for r in rows:
            print(dict(r))
        except Exception:
          try:
            result = await conn.execute(raw)
            print(result)
          except Exception as e2:
            print(f'Error: {e2}')

async def main():
  conn = await db.connect()
  try:
    await interactive_console(conn)
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
