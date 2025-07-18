from __future__ import annotations
import subprocess, os, sys, importlib.util, dotenv
from pathlib import Path

dotenv.load_dotenv()

dsn = os.environ["POSTGRES_CONNECTION_STRING"]


ROOT = Path(__file__).resolve().parent.parent

def main() -> None:
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
