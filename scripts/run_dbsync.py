from __future__ import annotations
import argparse
import asyncio
import os
from pathlib import Path
from typing import Iterable, NamedTuple

from scriptlib import apply_schema, connect, dump_schema, parse_version

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


class ScriptEntry(NamedTuple):
  path: Path
  version: str
  sort_key: tuple[int, int, int, int]


def _extract_version(name: str) -> str | None:
  stem = Path(name).stem
  if stem.startswith('to_'):
    candidate = stem[3:]
    return candidate or None
  if stem.startswith('v'):
    return stem.split('_', 1)[0]
  return None


def _find_candidate_scripts(paths: Iterable[Path]) -> list[ScriptEntry]:
  entries: list[ScriptEntry] = []
  for path in paths:
    if path.suffix.lower() != '.sql':
      continue
    version = _extract_version(path.name)
    if not version:
      continue
    try:
      sort_key = parse_version(version)
    except ValueError:
      continue
    entries.append(ScriptEntry(path=path, version=version, sort_key=sort_key))
  entries.sort(key=lambda entry: (entry.sort_key, entry.path.name))
  return entries


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


def _filter_pending(all_scripts: list[ScriptEntry], last_applied: str | None) -> list[ScriptEntry]:
  if not last_applied:
    return all_scripts
  last_version = _extract_version(last_applied)
  if not last_version:
    return all_scripts
  try:
    last_key = parse_version(last_version)
  except ValueError:
    return all_scripts
  return [entry for entry in all_scripts if entry.sort_key > last_key]


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
    for entry in pending:
      print(f'  - {entry.path.name}')

    if args.dry_run:
      return 0

    for entry in pending:
      print(f'Applying {entry.path.name}...')
      await apply_schema(conn, str(entry.path))
      await _upsert_config(conn, LAST_SCRIPT_KEY, entry.path.name)

    await _upsert_config(conn, SCHEMA_FLAG_KEY, '1')

    recorded_version = args.target_version or pending[-1].version
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
