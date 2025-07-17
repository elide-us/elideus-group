from __future__ import annotations
import asyncio
from scripts.database_cli import connect

async def main() -> None:
  conn = await connect()
  try:
    col = await conn.fetchrow(
      """
      SELECT column_name FROM information_schema.columns
      WHERE table_name='users_auth' AND column_name='provider_id';
      """
    )
    if col:
      print('users_auth already upgraded')
      return
    await conn.execute('ALTER TABLE users_auth RENAME TO users_auth_old')
    await conn.execute(
      """
      CREATE TABLE users_auth (
        user_guid UUID NOT NULL,
        provider_id INTEGER NOT NULL REFERENCES auth_provider(id),
        provider_user_id TEXT NOT NULL,
        PRIMARY KEY (provider_id, provider_user_id)
      );
      """
    )
    print('users_auth schema upgraded; run database_update.py to migrate data')
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
