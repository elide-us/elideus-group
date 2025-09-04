from __future__ import annotations
import subprocess, os, sys, importlib.util, asyncio, aioodbc, argparse
from pathlib import Path

def _unpack_version(ver: str) -> tuple[int, int, int, int]:
  ver = ver.lstrip('v')
  major, minor, patch, build = [int(p) for p in ver.split('.')]
  return major, minor, patch, build

def _next_build(current_version: str, last_version: str) -> int:
  """Return the next build number for the given versions.

  The build number is reset only when the major or minor version changes.
  Patch version bumps continue the build count within the same minor version.
  """
  current_major, current_minor, _, current_build = _unpack_version(current_version)
  last_major, last_minor, _, _ = _unpack_version(last_version)
  if (current_major, current_minor) != (last_major, last_minor):
    return 0
  return current_build + 1

def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--test', action='store_true',
    help='Run tests without updating build version'
  )
  return parser.parse_args()

async def update_build_version() -> None:
  from dotenv import load_dotenv
  load_dotenv()

  pool = None
  try:
    dsn = os.environ["AZURE_SQL_CONNECTION_STRING"]
    pool = await aioodbc.create_pool(dsn=dsn, autocommit=True)
  except Exception as e:
    print(f'Unable to connect to database: {e}')
    return

  try:
    async with pool.acquire() as conn:
      async with conn.cursor() as cur:
        await cur.execute(
          "SELECT element_value FROM system_config WHERE element_key='Version'"
        )
        row = await cur.fetchone()
        current_version = row[0] if row else None

        await cur.execute(
          "SELECT element_value FROM system_config WHERE element_key='LastVersion'"
        )
        row = await cur.fetchone()
        last_version = row[0] if row else None

        if not current_version:
          print('Version entry not found in config table')
          return
        if not last_version:
          last_version = current_version

        current_major, current_minor, current_patch, _ = parse_version(current_version)
        build = next_build(current_version, last_version)

        new_version = f"v{current_major}.{current_minor}.{current_patch}.{build}"
        print(f'Updating build version: {current_version} -> {new_version}')

        await cur.execute(
          "UPDATE system_config SET element_value=? WHERE element_key='Version'",
          (new_version,),
        )
        if cur.rowcount == 0:
          print('Failed to update config record Version')
          return

        await cur.execute(
          "UPDATE system_config SET element_value=? WHERE element_key='LastVersion'",
          (current_version,),
        )
        if cur.rowcount == 0:
          print('Failed to update config record LastVersion')
          return
        # await _update_config_database(conn, 'Version', new_version)
        # await _update_config_database(conn, 'LastVersion', current_version)
  finally:
    if pool:
      pool.close()
      await pool.wait_closed()

def main() -> None:
  ROOT = Path(__file__).resolve().parent.parent

  args = _parse_args()
  if not args.test:
    asyncio.run(update_build_version())

  subprocess.check_call([sys.executable, 'scripts/generate_rpc_library.py'], cwd=ROOT)
  subprocess.check_call([sys.executable, 'scripts/generate_rpc_client.py'], cwd=ROOT)
  
  subprocess.check_call(['npm', 'run', 'lint'], cwd=ROOT / 'frontend')
  subprocess.check_call(['npm', 'run', 'type-check'], cwd=ROOT / 'frontend')

  try:
    subprocess.check_call(['npx', 'vitest', 'run', '--coverage'], cwd=ROOT / 'frontend')
  except subprocess.CalledProcessError:
    print('vitest coverage failed, running without coverage')
    subprocess.check_call(['npx', 'vitest', 'run'], cwd=ROOT / 'frontend')

  if importlib.util.find_spec('pytest_cov'):
    subprocess.check_call(['pytest', '--cov=.', '--cov-report=term-missing', '-q'], cwd=ROOT)
  else:
    print('pytest-cov not installed, running without coverage')
    subprocess.check_call(['pytest', '-q'], cwd=ROOT)

if __name__ == '__main__':
  main()
