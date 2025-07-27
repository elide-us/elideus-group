from __future__ import annotations
import os, json, aioodbc, dotenv
from datetime import datetime, timezone

dotenv.load_dotenv()

async def list_tables(conn):
  async with conn.cursor() as cur:
    await cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    rows = await cur.fetchall()
  return [{'table_name': r[0]} for r in rows]

async def list_columns(conn, table):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT COLUMN_NAME, DATA_TYPE
         FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION""",
      (table,)
    )
    rows = await cur.fetchall()
  return [{'column_name': r[0], 'data_type': r[1]} for r in rows]

async def list_indexes(conn, table):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT name, type_desc FROM sys.indexes
         WHERE object_id = OBJECT_ID(?)""",
      (table,)
    )
    rows = await cur.fetchall()
  return [{'indexname': r[0], 'indexdef': r[1]} for r in rows]

async def _table_schema(conn, table: str):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
         FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION""",
      (table,)
    )
    cols = await cur.fetchall()
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT k.COLUMN_NAME
         FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
         JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
           ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
         WHERE t.TABLE_NAME=? AND t.CONSTRAINT_TYPE='PRIMARY KEY'""",
      (table,)
    )
    pk = await cur.fetchall()
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT k.COLUMN_NAME, c.TABLE_NAME, c.COLUMN_NAME
         FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS r
         JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k ON r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
         JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE c ON r.UNIQUE_CONSTRAINT_NAME = c.CONSTRAINT_NAME
         WHERE k.TABLE_NAME=?""",
      (table,)
    )
    fks = await cur.fetchall()
  return {
    'name': table,
    'columns': [
      {
        'name': c[0],
        'type': c[1],
        'nullable': c[2] == 'YES',
        'default': c[3],
      }
      for c in cols
    ],
    'primary_key': [r[0] for r in pk],
    'foreign_keys': [
      {
        'column': fk[0],
        'ref_table': fk[1],
        'ref_column': fk[2],
      }
      for fk in fks
    ],
  }

async def get_schema(conn):
  tables = await list_tables(conn)
  schemas: dict[str, dict] = {}
  deps: dict[str, set[str]] = {}
  for t in tables:
    name = t['table_name']
    info = await _table_schema(conn, name)
    schemas[name] = info
    deps[name] = {fk['ref_table'] for fk in info['foreign_keys']}
  ordered: list[str] = []
  visited: set[str] = set()
  def visit(n: str):
    if n in visited:
      return
    visited.add(n)
    for d in deps.get(n, set()):
      if d in deps:
        visit(d)
    ordered.append(n)
  for t in deps.keys():
    visit(t)
  return {'tables': [schemas[n] for n in ordered]}

def _build_create_sql(table: dict) -> str:
  parts: list[str] = []
  for col in table['columns']:
    line = f"{col['name']} {col['type']}"
    if col['default'] is not None:
      line += f" DEFAULT {col['default']}"
    if not col['nullable']:
      line += ' NOT NULL'
    parts.append(line)
  if table['primary_key']:
    parts.append('PRIMARY KEY (' + ', '.join(table['primary_key']) + ')')
  for fk in table['foreign_keys']:
    parts.append(
      f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['ref_table']}({fk['ref_column']})"
    )
  return f"CREATE TABLE {table['name']} ({', '.join(parts)})"

async def dump_schema(conn, prefix: str = 'schema') -> str:
  schema = await get_schema(conn)
  ts = datetime.now(timezone.utc).strftime('%Y%m%d')
  filename = f"{prefix}_{ts}.json"
  with open(filename, 'w') as f:
    json.dump(schema, f, indent=2)
  print(f'Schema dumped to {filename}')
  return filename

async def dump_data(conn, prefix: str = 'dump_data') -> str:
  schema = await get_schema(conn)
  data: dict[str, list[dict]] = {}
  for tbl in schema['tables']:
    name = tbl['name']
    async with conn.cursor() as cur:
      await cur.execute(f"SELECT * FROM {name}")
      rows = await cur.fetchall()
    cols = [d[0] for d in cur.description]
    data[name] = [dict(zip(cols, r)) for r in rows]
  ts = datetime.now(timezone.utc).strftime('%Y%m%d_BACKUP')
  filename = f"{prefix}_{ts}.json"
  with open(filename, 'w') as f:
    json.dump({'schema': schema, 'data': data}, f, indent=2, default=str)
  print(f'Data dumped to {filename}')
  return filename

async def apply_schema(conn, path: str):
  with open(path, 'r') as f:
    schema = json.load(f)
  for table in schema.get('tables', []):
    async with conn.cursor() as cur:
      await cur.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=?",
        (table['name'],),
      )
      exists = await cur.fetchone()
    if not exists:
      async with conn.cursor() as cur:
        await cur.execute(_build_create_sql(table))
    else:
      cols = await list_columns(conn, table['name'])
      existing = {c['column_name'] for c in cols}
      for col in table['columns']:
        if col['name'] not in existing:
          line = f"ALTER TABLE {table['name']} ADD {col['name']} {col['type']}"
          if col['default'] is not None:
            line += f" DEFAULT {col['default']}"
          if not col['nullable']:
            line += ' NOT NULL'
          async with conn.cursor() as cur:
            await cur.execute(line)
  print('Schema applied.')

async def connect(dbname=None):
  dsn = os.getenv('AZURE_SQL_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('AZURE_SQL_CONNECTION_STRING not set')
  if dbname:
    parts = []
    replaced = False
    for part in dsn.split(';'):
      if part.upper().startswith('DATABASE=') or part.upper().startswith('INITIAL CATALOG='):
        parts.append(f'DATABASE={dbname}')
        replaced = True
      else:
        parts.append(part)
    if not replaced:
      parts.append(f'DATABASE={dbname}')
    dsn = ';'.join(parts)
  conn = await aioodbc.connect(dsn=dsn, autocommit=True)
  print(f'Connected to database {dbname or dsn}')
  return conn
