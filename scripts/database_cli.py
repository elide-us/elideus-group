from __future__ import annotations
import os, json, asyncio, asyncpg, dotenv

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
