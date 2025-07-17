from __future__ import annotations
import os, asyncio, asyncpg, dotenv
dotenv.load_dotenv()

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  guid UUID UNIQUE NOT NULL,
  email TEXT NOT NULL,
  display_name TEXT,
  auth_provider INTEGER
);

CREATE TABLE IF NOT EXISTS users_auth (
  user_guid UUID PRIMARY KEY REFERENCES users(guid),
  microsoft_id TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS users_credits (
  user_guid UUID PRIMARY KEY REFERENCES users(guid),
  credits INTEGER NOT NULL DEFAULT 0
);
'''

async def main() -> None:
  dsn = os.getenv('POSTGRES_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('POSTGRES_CONNECTION_STRING not set')

  sql = SCHEMA
  conn = await asyncpg.connect(dsn=dsn)
  try:
    await conn.execute(sql)
    print('✅ Database schema applied')
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
