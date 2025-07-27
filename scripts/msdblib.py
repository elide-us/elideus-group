from __future__ import annotations
import os, json, aioodbc, dotenv
from datetime import datetime, timezone

dotenv.load_dotenv()

async def list_tables(conn):
  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT TABLE_NAME AS table_name FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' FOR JSON PATH"
    )
    row = await cur.fetchone()
  return json.loads(row[0]) if row else []

async def list_columns(conn, table):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT COLUMN_NAME AS column_name, DATA_TYPE AS data_type
         FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
  return json.loads(row[0]) if row else []

async def list_indexes(conn, table):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT name AS indexname, type_desc AS indexdef
         FROM sys.indexes WHERE object_id = OBJECT_ID(?) FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
  return json.loads(row[0]) if row else []

async def list_keys(conn, table):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT k.CONSTRAINT_NAME AS constraint_name,
                k.COLUMN_NAME AS column_name,
                tc.CONSTRAINT_TYPE AS constraint_type
         FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
         JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
           ON k.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
         WHERE k.TABLE_NAME=? FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
  return json.loads(row[0]) if row else []

async def list_constraints(conn, table):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT CONSTRAINT_NAME AS constraint_name,
                CONSTRAINT_TYPE AS constraint_type
         FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
         WHERE TABLE_NAME=? FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
  return json.loads(row[0]) if row else []

async def _table_schema(conn, table: str):
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT COLUMN_NAME AS name,
                DATA_TYPE AS type,
                IS_NULLABLE AS nullable,
                COLUMN_DEFAULT AS [default]
         FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
    cols = json.loads(row[0]) if row else []
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT k.COLUMN_NAME AS column_name
         FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS t
         JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
           ON t.CONSTRAINT_NAME = k.CONSTRAINT_NAME
         WHERE t.TABLE_NAME=? AND t.CONSTRAINT_TYPE='PRIMARY KEY' FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
    pk = json.loads(row[0]) if row else []
  async with conn.cursor() as cur:
    await cur.execute(
      """SELECT k.COLUMN_NAME AS column_name,
                c.TABLE_NAME AS ref_table,
                c.COLUMN_NAME AS ref_column
         FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS r
         JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k ON r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
         JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE c ON r.UNIQUE_CONSTRAINT_NAME = c.CONSTRAINT_NAME
         WHERE k.TABLE_NAME=? FOR JSON PATH""",
      (table,),
    )
    row = await cur.fetchone()
    fks = json.loads(row[0]) if row else []
  return {
    'name': table,
    'columns': [
      {
        'name': c['name'],
        'type': c['type'],
        'nullable': c['nullable'] == 'YES',
        'default': c['default'],
      }
      for c in cols
    ],
    'primary_key': [r['column_name'] for r in pk],
    'foreign_keys': [
      {
        'column': fk['column_name'],
        'ref_table': fk['ref_table'],
        'ref_column': fk['ref_column'],
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
      await cur.execute(f"SELECT * FROM {name} FOR JSON PATH")
      row = await cur.fetchone()
    data[name] = json.loads(row[0]) if row else []
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
