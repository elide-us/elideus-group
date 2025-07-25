from __future__ import annotations
import subprocess, os, sys, importlib.util, asyncio, asyncpg, argparse
from pathlib import Path

def _unpack_version(ver: str) -> tuple[int, int, int, int]:
  ver = ver.lstrip('v')
  major, minor, patch, build = [int(p) for p in ver.split('.')]
  return major, minor, patch, build

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

  try:
    dsn = os.environ["POSTGRES_CONNECTION_STRING"]
    pool = await asyncpg.create_pool(dsn=dsn)
  except Exception as e:
    print(f'Unable to connect to database: {e}')
    return
  async with pool.acquire() as conn:
    current_version = await conn.fetchval("SELECT value FROM config WHERE key='Version'")
    last_version = await conn.fetchval("SELECT value FROM config WHERE key='LastVersion'")
    if not current_version:
      print('Version entry not found in config table')
      await pool.close()
      return
    if not last_version:
      last_version = current_version
    current_major, current_minor, current_patch, current_build = _unpack_version(current_version)
    last_major, last_minor, last_patch, _ = _unpack_version(last_version)
    if (current_major, current_minor, current_patch) != (last_major, last_minor, last_patch):
      build = 1
    else:
      build = current_build + 1
    
    new_version = f"v{current_major}.{current_minor}.{current_patch}.{build}"
    print(f'Updating build version: {current_version} -> {new_version}')

    res = await conn.execute("UPDATE config SET value=$1 WHERE key='Version'", new_version)
    if res.startswith("UPDATE 0"):
      print("Failed to update config record Version")
      return

    res = await conn.execute("UPDATE config SET value=$1 WHERE key='LastVersion'", current_version)
    if res.startswith("UPDATE 0"):
      print("Failed to update config record LastVersion")
      return
    # await _update_config_database(conn, 'Version', new_version)
    # await _update_config_database(conn, 'LastVersion', current_version)
  await pool.close()

def main() -> None:
  ROOT = Path(__file__).resolve().parent.parent

  args = _parse_args()
  if not args.test:
    asyncio.run(update_build_version())

  subprocess.check_call([sys.executable, 'scripts/generate_rpc_library.py'], cwd=ROOT)
  subprocess.check_call([sys.executable, 'scripts/generate_rpc_client.py'], cwd=ROOT)
  subprocess.check_call([sys.executable, 'scripts/generate_rpc_metadata.py'], cwd=ROOT)
  
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
