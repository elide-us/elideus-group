from __future__ import annotations
import asyncio
from dblib import connect
from server.helpers import roles as role_helper

async def main() -> None:
  conn = await connect()
  async with conn.transaction():
    for name, mask in role_helper.DEFAULT_ROLES.items():
      await conn.execute(
        "INSERT INTO roles(name, mask) VALUES($1, $2) ON CONFLICT(name) DO UPDATE SET mask=excluded.mask;",
        name,
        mask,
      )
  await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
