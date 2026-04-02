from __future__ import annotations

"""Generate frontend route registry from frontend_pages table."""

import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

from common import HEADER_COMMENT, REPO_ROOT

load_dotenv(os.path.join(REPO_ROOT, '.env'))

OUTPUT_DIR = Path(REPO_ROOT) / 'frontend' / 'src' / 'routes'
OUTPUT_PATH = OUTPUT_DIR / 'registry.ts'

QUERY = """
SELECT element_path, element_component
FROM frontend_pages
ORDER BY element_sequence
""".strip()


def connect() -> pyodbc.Connection:
  dsn = os.environ.get('AZURE_SQL_CONNECTION_STRING_DEV') or os.environ.get('AZURE_SQL_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('Missing AZURE_SQL_CONNECTION_STRING_DEV/AZURE_SQL_CONNECTION_STRING in environment')
  return pyodbc.connect(dsn, autocommit=True)


def fetch_frontend_pages() -> list[tuple[str, str]]:
  conn = connect()
  try:
    cursor = conn.cursor()
    rows = cursor.execute(QUERY).fetchall()
    return [(str(row[0]), str(row[1])) for row in rows]
  finally:
    conn.close()


def generate_registry(rows: list[tuple[str, str]]) -> str:
  lines = HEADER_COMMENT.copy()
  if rows:
    lines.append("import { lazy, type ComponentType, type LazyExoticComponent } from 'react';")
  else:
    lines.append("import { type ComponentType, type LazyExoticComponent } from 'react';")
  lines.append('')
  lines.append('type PageRoute = {')
  lines.append('\tpath: string;')
  lines.append('\tcomponent: LazyExoticComponent<ComponentType<any>>;')
  lines.append('};')
  lines.append('')
  lines.append('const PAGE_ROUTES: PageRoute[] = [')
  for path, component in rows:
    lines.append(f"\t{{ path: '{path}', component: lazy(() => import('../pages/{component}')) }},")
  lines.append('];')
  lines.append('')
  lines.append('export default PAGE_ROUTES;')
  lines.append('')
  return '\n'.join(lines)


def write_registry(rows: list[tuple[str, str]]) -> None:
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  OUTPUT_PATH.write_text(generate_registry(rows), encoding='utf-8')


def main() -> None:
  try:
    rows = fetch_frontend_pages()
  except Exception as exc:
    print(f'[SKIP] Could not query frontend_pages: {exc}')
    print('  This is expected in environments without ODBC (e.g., Codex CI).')
    print('  Writing an empty route registry so frontend type-checks can continue.')
    write_registry([])
    print(f'Wrote 0 route entries to {OUTPUT_PATH}')
    return

  write_registry(rows)
  print(f'Wrote {len(rows)} route entries to {OUTPUT_PATH}')


if __name__ == '__main__':
  main()
