from __future__ import annotations
import argparse, asyncio
from dblib import connect, apply_schema

async def main(path: str) -> None:
  conn = await connect()
  await apply_schema(conn, path)
  await conn.close()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('path', help='Schema JSON path')
  args = parser.parse_args()
  asyncio.run(main(args.path))
