from __future__ import annotations
import argparse, asyncio, os
from pathlib import Path
from typing import Iterable
from scriptlib import connect, apply_schema, dump_schema

SCHEMA_FLAG_KEY = 'PendingSchemaDump'
SCHEMA_VERSION_KEY = 'PendingSchemaVersion'
LAST_SCRIPT_KEY = 'SchemaLastApplied'


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Apply database upgrade scripts')
  parser.add_argument(
    '--dry-run',
    action='store_true',
    help='List pending SQL scripts without applying them',
  )
  parser.add_argument(
    '--dump-schema',
    action='store_true',
    help='Dump the schema after applying migrations',
  )
  parser.add_argument(
    '--target-version',
    help='Explicit schema version to record after sync',
  )
  parser.add_argument(
    '--scripts-dir',
    default=Path(__file__).resolve().parent,
    type=Path,
    help='Directory to scan for upgrade SQL scripts',
  )
  return parser.parse_args()


def _find_candidate_scripts(paths: Iterable[Path]) -> list[Path]:
  return sorted([p for p in paths if p.suffix == '.sql' and p.name.startswith('to_')])


async def _fetch_config(conn, key: str) -> str | None:
  async with conn.cursor() as cur:
    await cur.execute('SELECT element_value FROM system_config WHERE element_key=?', (key,))
    row = await cur.fetchone()
    return row[0] if row else None


async def _upsert_config(conn, key: str, value: str) -> None:
  async with conn.cursor() as cur:
    await cur.execute('UPDATE system_config SET element_value=? WHERE element_key=?', (value, key))
    if cur.rowcount == 0:
      await cur.execute(
        'INSERT INTO system_config(element_key, element_value) VALUES(?, ?)',
        (key, value),
      )


def _filter_pending(all_scripts: list[Path], last_applied: str | None) -> list[Path]:
  if not last_applied:
    return all_scripts
  return [path for path in all_scripts if path.name > last_applied]


def _infer_version(name: str) -> str | None:
  base = name.split('.', 1)[0]
  if base.startswith('to_'):
    candidate = base[3:]
    if candidate:
      return candidate
  return None


async def main() -> int:
  args = _parse_args()
  scripts_dir = args.scripts_dir
  if not scripts_dir.exists():
    raise SystemExit(f'Scripts directory {scripts_dir} does not exist')

  candidates = _find_candidate_scripts(scripts_dir.iterdir())
  if not candidates:
    print('No schema upgrade scripts found.')
    return 0

  conn = await connect()
  try:
    last_applied = await _fetch_config(conn, LAST_SCRIPT_KEY)
    pending = _filter_pending(candidates, last_applied)
    if not pending:
      print('No pending schema scripts to apply.')
      return 0

    print('Pending schema scripts:')
    for script in pending:
      print(f'  - {script.name}')

    if args.dry_run:
      return 0

    for script in pending:
      print(f'Applying {script.name}...')
      await apply_schema(conn, str(script))
      await _upsert_config(conn, LAST_SCRIPT_KEY, script.name)

    await _upsert_config(conn, SCHEMA_FLAG_KEY, '1')

    recorded_version = args.target_version or _infer_version(pending[-1].name)
    if recorded_version:
      await _upsert_config(conn, SCHEMA_VERSION_KEY, recorded_version)

    if args.dump_schema:
      if recorded_version:
        prefix = f'schema_{recorded_version}'
      else:
        prefix = os.getenv('SCHEMA_DUMP_PREFIX', 'schema')
      await dump_schema(conn, prefix)

    print('Database sync complete.')
    return len(pending)
  finally:
    await conn.close()


if __name__ == '__main__':
  try:
    applied = asyncio.run(main())
  except KeyboardInterrupt:
    raise SystemExit(1)
  raise SystemExit(0 if applied >= 0 else 1)
