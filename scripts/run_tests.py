from __future__ import annotations
import subprocess, os, sys, importlib.util, dotenv, asyncio, asyncpg, argparse
from pathlib import Path

dotenv.load_dotenv()

dsn = os.environ["POSTGRES_CONNECTION_STRING"]


def _parse_version(ver: str) -> tuple[int, int, int, int]:
  ver = ver.lstrip('v')
  major, minor, patch, build = [int(p) for p in ver.split('.')]
  return major, minor, patch, build


async def _update_config(conn, key: str, value: str):
  res = await conn.execute(
    "UPDATE config SET value=$1 WHERE key=$2", value, key
  )
  if res.startswith("UPDATE 0"):
    await conn.execute(
      "INSERT INTO config(key, value) VALUES($1, $2)", key, value
    )


async def update_build_version() -> None:
  try:
    pool = await asyncpg.create_pool(dsn=dsn)
  except Exception as e:
    print(f'Unable to connect to database: {e}')
    return
  async with pool.acquire() as conn:
    cur = await conn.fetchval("SELECT value FROM config WHERE key='Version'")
    last = await conn.fetchval("SELECT value FROM config WHERE key='LastVersion'")
    if not cur:
      print('Version entry not found in config table')
      await pool.close()
      return
    if not last:
      last = cur
    cur_m, cur_n, cur_p, cur_b = _parse_version(cur)
    last_m, last_n, last_p, _ = _parse_version(last)
    if (cur_m, cur_n, cur_p) != (last_m, last_n, last_p):
      build = 1
    else:
      build = cur_b + 1
    new_ver = f"v{cur_m}.{cur_n}.{cur_p}.{build}"
    print(f'Updating build version: {cur} -> {new_ver}')
    await _update_config(conn, 'Version', new_ver)
    await _update_config(conn, 'LastVersion', cur)
  await pool.close()


ROOT = Path(__file__).resolve().parent.parent

def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--test', action='store_true',
    help='Run tests without updating build version'
  )
  return parser.parse_args()


def main() -> None:
  args = parse_args()
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
