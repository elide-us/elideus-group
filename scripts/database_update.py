from __future__ import annotations
import asyncio
from database_cli import connect

async def column_exists(conn, table: str, column: str) -> bool:
  row = await conn.fetchrow(
    """
    SELECT 1 FROM information_schema.columns
    WHERE table_name=$1 AND column_name=$2;
    """,
    table,
    column,
  )
  return row is not None

async def main() -> None:
  conn = await connect()
  try:
    exists = await conn.fetchrow(
      "SELECT to_regclass('users_auth_old') AS t"
    )
    if not exists or not exists['t']:
      print('users_auth_old not found; nothing to migrate')
      return
    providers = await conn.fetch('SELECT id, name FROM auth_provider')
    for p in providers:
      col = f"{p['name']}_id"
      if await column_exists(conn, 'users_auth_old', col):
        await conn.execute(
          f"""
          INSERT INTO users_auth (user_guid, provider_id, provider_user_id)
          SELECT user_guid, {p['id']}, {col}
          FROM users_auth_old
          WHERE {col} IS NOT NULL;
          """
        )
    await conn.execute('DROP TABLE users_auth_old')
    print('users_auth data migrated')
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
