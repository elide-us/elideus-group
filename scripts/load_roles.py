from __future__ import annotations
import asyncio
from dblib import connect
from server.helpers.roles import ROLE_DEFAULTS

async def main() -> None:
  conn = await connect()
  async with conn.transaction():
    for name, mask in ROLE_DEFAULTS.items():
      await conn.execute(
        "INSERT INTO roles(name, mask) VALUES($1, $2) "
        "ON CONFLICT(name) DO UPDATE SET mask=excluded.mask;",
        name,
        mask,
      )
  await conn.close()
  print("Roles loaded.")

if __name__ == '__main__':
  asyncio.run(main())
