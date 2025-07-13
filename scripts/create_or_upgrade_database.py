from __future__ import annotations
import os, asyncio, asyncpg, dotenv
from pathlib import Path

dotenv.load_dotenv()

SCHEMA_PATH = Path(__file__).resolve().parent.parent / 'db' / 'schema.sql'

async def main() -> None:
  dsn = os.getenv('POSTGRES_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('POSTGRES_CONNECTION_STRING not set')

  sql = SCHEMA_PATH.read_text()
  conn = await asyncpg.connect(dsn=dsn)
  try:
    await conn.execute(sql)
    print('✅ Database schema applied')
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
