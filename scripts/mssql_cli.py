from __future__ import annotations
import argparse, asyncio, os, subprocess, pyodbc
from scriptlib import connect, dump_schema, apply_schema, dump_data, bump_version


def _ensure_env_var(name: str, env: str) -> None:
  if env == 'test':
    source = f'{name}_DEV'
    value = os.getenv(source)
    if not value:
      raise RuntimeError(f'{source} not set')
    os.environ[name] = value
  else:
    value = os.getenv(name)
    if not value:
      raise RuntimeError(f'{name} not set')


def _configure_environment(env: str) -> None:
  if env not in {'test', 'prod'}:
    raise ValueError(f"Unknown environment '{env}'")
  _ensure_env_var('AZURE_SQL_CONNECTION_STRING', env)
  _ensure_env_var('DISCORD_SECRET', env)


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Interactive MSSQL management CLI')
  parser.add_argument(
    '-e',
    '--env',
    default='test',
    choices=['test', 'prod'],
    help='Environment to target (default: test)',
  )
  return parser.parse_args()


def _commit_and_tag(version: str, schema_file: str) -> None:
  subprocess.check_call(f'git add {schema_file}', shell=True)
  subprocess.check_call(f'git commit -m "Exported DB schema for {version}"', shell=True)
  subprocess.check_call(f'git tag {version}', shell=True)

  current_branch = subprocess.check_output(
    "git rev-parse --abbrev-ref HEAD", shell=True, text=True
  ).strip()
  subprocess.check_call(f'git push origin {current_branch}', shell=True)
  subprocess.check_call('git push origin --tags', shell=True)


def _wide_to_str(value):
  if value is None:
    return None
  if isinstance(value, (bytes, bytearray, memoryview)):
    return bytes(value).decode('utf-16-le', errors='ignore').rstrip('\x00')
  return value


async def _update_config(conn, key: str, value: str):
  async with conn.cursor() as cur:
    await cur.execute(
      "UPDATE system_config SET element_value=? WHERE element_key=?",
      (value, key),
    )
    if cur.rowcount == 0:
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
        await dump_schema(conn)
      case ['schema', 'dump', name]:
        await dump_schema(conn, name)
      case ['schema', 'apply', file]:
        try:
          await apply_schema(conn, file)
        except Exception as e:
          print(f'Error applying schema: {e}')
      case ['dump', 'data']:
        await dump_data(conn)
      case ['dump', 'data', name]:
        await dump_data(conn, name)
      case ['update', 'version', part] if part in {'major', 'minor', 'patch'}:
        async with conn.cursor() as cur:
          await cur.execute("SELECT element_value FROM system_config WHERE element_key='Version'")
          row = await cur.fetchone()
        if not row:
          print('Version entry not found in system_config table')
          continue
        cur_ver = row[0]
        new_ver = bump_version(cur_ver, part)
        await _update_config(conn, 'Version', new_ver)
        print(f'Updated Version: {cur_ver} -> {new_ver}')
        schema_file = await dump_schema(conn, new_ver)
        _commit_and_tag(new_ver, schema_file)
      case _:
        try:
          async with conn.cursor() as cur:
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

async def main():
  args = _parse_args()
  _configure_environment(args.env)
  pyodbc.add_output_converter(-16, _wide_to_str)
  conn = await connect()
  try:
    await interactive_console(conn)
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
