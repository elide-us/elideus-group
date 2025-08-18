from __future__ import annotations
import asyncio
import pgdblib as db

HELP_TEXT = """
Available commands:
  help                               Show this help message
  exit, quit                         Exit the console
  reconnect <db>                     Connect to a different database
  list tables                        List all tables
  list columns <table>               List columns of a table
  list indexes <table>               List indexes on a table
  index all                          Reindex the current database
  schema dump [name]                 Dump DB schema to <name>_YYYYMMDD.json
  schema apply <file>                Apply schema JSON to the database
  dump data [name]                   Dump DB schema and rows to <name>_YYYYMMDD.json
  dump mssql [name]                  Dump data formatted for MSSQL import
"""

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
      case ['reconnect', dbname]:
        try:
          await conn.close()
          conn = await db.connect(dbname)
        except Exception as e:
          print(f'Error reconnecting: {e}')
      case ['list', 'tables']:
        rows = await db.list_tables(conn)
        for r in rows:
          print(r['table_name'])
      case ['list', 'columns', table]:
        rows = await db.list_columns(conn, table)
        for r in rows:
          print(f"{r['column_name']} ({r['data_type']})")
      case ['list', 'indexes', table]:
        rows = await db.list_indexes(conn, table)
        for r in rows:
          print(f"{r['indexname']} ({r['indexdef']})")
      case ['index', 'all']:
        await conn.execute('REINDEX DATABASE current_database()')
        print('Reindex complete.')
      case ['schema', 'dump']:
        await db.dump_schema(conn)
      case ['schema', 'dump', name]:
        await db.dump_schema(conn, name)
      case ['schema', 'apply', file]:
        try:
          await db.apply_schema(conn, file)
        except Exception as e:
          print(f'Error applying schema: {e}')
      case ['dump', 'data']:
        await db.dump_data(conn)
      case ['dump', 'data', name]:
        await db.dump_data(conn, name)
      case ['dump', 'mssql']:
        await db.dump_mssql(conn)
      case ['dump', 'mssql', name]:
        await db.dump_mssql(conn, name)
      case _:
        try:
          rows = await conn.fetch(raw)
          for r in rows:
            print(dict(r))
        except Exception:
          try:
            result = await conn.execute(raw)
            print(result)
          except Exception as e2:
            print(f'Error: {e2}')

async def main():
  conn = await db.connect()
  try:
    await interactive_console(conn)
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
