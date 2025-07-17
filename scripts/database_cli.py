from __future__ import annotations
import os, json, asyncio, asyncpg, dotenv, datetime

dotenv.load_dotenv()

HELP_TEXT = """
Available commands:
  help                               Show this help message
  exit, quit                         Exit the console
  reconnect <db>                     Connect to a different database
  list tables                        List all tables
  list columns <table>               List columns of a table
  list indexes <table>               List indexes on a table
  index all                          Reindex the current database
  schema dump [name]                 Dump DB schema to name_TIMESTAMP.json
  schema apply <file>                Apply schema JSON to the database
"""

async def list_tables(conn):
  query = """
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public';
  """
  return await conn.fetch(query)

async def list_columns(conn, table):
  query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name=$1;
  """
  return await conn.fetch(query, table)

async def list_indexes(conn, table):
  query = """
    SELECT indexname, indexdef
    FROM pg_indexes WHERE tablename=$1;
  """
  return await conn.fetch(query, table)

async def _table_schema(conn, table: str):
  cols = await conn.fetch(
    """
      SELECT column_name, data_type, is_nullable, column_default
      FROM information_schema.columns
      WHERE table_name=$1 AND table_schema='public'
      ORDER BY ordinal_position;
    """,
    table,
  )
  pk = await conn.fetch(
    """
      SELECT a.attname
      FROM pg_index i
      JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
      WHERE i.indrelid = $1::regclass AND i.indisprimary;
    """,
    table,
  )
  fks = await conn.fetch(
    """
      SELECT kcu.column_name, ccu.table_name AS foreign_table_name,
             ccu.column_name AS foreign_column_name
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
       AND tc.table_schema = kcu.table_schema
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
       AND ccu.table_schema = tc.table_schema
      WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_name=$1;
    """,
    table,
  )
  return {
    'name': table,
    'columns': [
      {
        'name': c['column_name'],
        'type': c['data_type'],
        'nullable': c['is_nullable'] == 'YES',
        'default': c['column_default'],
      }
      for c in cols
    ],
    'primary_key': [r['attname'] for r in pk],
    'foreign_keys': [
      {
        'column': fk['column_name'],
        'ref_table': fk['foreign_table_name'],
        'ref_column': fk['foreign_column_name'],
      }
      for fk in fks
    ],
  }

async def get_schema(conn):
  tables = await list_tables(conn)
  schemas = {}
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
  parts = []
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
  cols = ', '.join(parts)
  return f"CREATE TABLE IF NOT EXISTS {table['name']} ({cols});"

async def dump_schema(conn, prefix: str = 'schema') -> str:
  schema = await get_schema(conn)
  ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
  filename = f"{prefix}_{ts}.json"
  with open(filename, 'w') as f:
    json.dump(schema, f, indent=2)
  print(f'Schema dumped to {filename}')
  return filename

async def apply_schema(conn, path: str):
  with open(path, 'r') as f:
    schema = json.load(f)
  async with conn.transaction():
    for table in schema.get('tables', []):
      exists = await conn.fetchval(
        """SELECT 1 FROM information_schema.tables
           WHERE table_schema='public' AND table_name=$1""",
        table['name'],
      )
      if not exists:
        await conn.execute(_build_create_sql(table))
      else:
        cols = await list_columns(conn, table['name'])
        existing = {c['column_name'] for c in cols}
        for col in table['columns']:
          if col['name'] not in existing:
            line = f"ALTER TABLE {table['name']} ADD COLUMN {col['name']} {col['type']}"
            if col['default'] is not None:
              line += f" DEFAULT {col['default']}"
            if not col['nullable']:
              line += ' NOT NULL'
            line += ';'
            await conn.execute(line)
  print('Schema applied.')

async def connect(dbname=None):
  dsn = os.getenv('POSTGRES_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('POSTGRES_CONNECTION_STRING not set')
  if dbname:
    parts = dsn.rsplit('/', 1)
    dsn = '/'.join([parts[0], dbname])
  conn = await asyncpg.connect(dsn=dsn)
  print(f'Connected to database {dbname or dsn.rsplit("/",1)[1]}.')
  return conn

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
      case ['reconnect', db]:
        try:
          await conn.close()
          conn = await connect(db)
        except Exception as e:
          print(f'Error reconnecting: {e}')
      case ['list', 'tables']:
        rows = await list_tables(conn)
        for r in rows:
          print(r['table_name'])
      case ['list', 'columns', table]:
        rows = await list_columns(conn, table)
        for r in rows:
          print(f"{r['column_name']} ({r['data_type']})")
      case ['list', 'indexes', table]:
        rows = await list_indexes(conn, table)
        for r in rows:
          print(f"{r['indexname']} ({r['indexdef']})")
      case ['index', 'all']:
        await conn.execute('REINDEX DATABASE current_database()')
        print('Reindex complete.')
      case ['schema', 'dump']:
        await dump_schema(conn)
      case ['schema', 'dump', name]:
        await dump_schema(conn, name)
      case ['schema', 'apply', file]:
        try:
          await apply_schema(conn, file)
        except Exception as e:
          print(f'Error applying schema: {e}')
      case _:
        try:
          rows = await conn.fetch(raw)
          for r in rows:
            print(dict(r))
        except Exception as e:
          try:
            result = await conn.execute(raw)
            print(result)
          except Exception as e2:
            print(f'Error: {e2}')

async def main():
  conn = await connect()
  try:
    await interactive_console(conn)
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
