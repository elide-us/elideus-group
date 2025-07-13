from __future__ import annotations
import os, asyncio, json, asyncpg, dotenv

dotenv.load_dotenv()

async def interrogate() -> None:
  dsn = os.getenv('POSTGRES_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('POSTGRES_CONNECTION_STRING not set')

  conn = await asyncpg.connect(dsn=dsn)
  try:
    tables = await conn.fetch(
      """
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema='public'
      ORDER BY table_name;
      """
    )

    schema: dict[str, dict[str, list[dict[str, str]]]] = {}
    for record in tables:
      table = record['table_name']
      columns = await conn.fetch(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=$1
        ORDER BY ordinal_position;
        """,
        table,
      )
      indexes = await conn.fetch(
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname='public' AND tablename=$1;
        """,
        table,
      )
      schema[table] = {
        'columns': [dict(row) for row in columns],
        'indexes': [dict(row) for row in indexes],
      }

    print(json.dumps(schema, indent=2))
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(interrogate())
