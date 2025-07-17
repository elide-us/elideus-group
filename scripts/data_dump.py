from __future__ import annotations
import asyncio, json, datetime
from database_cli import connect, get_schema

async def main(prefix: str = 'backup') -> None:
  conn = await connect()
  try:
    schema = await get_schema(conn)
    data: dict[str, list[dict]] = {}
    for table in [t['name'] for t in schema['tables']]:
      rows = await conn.fetch(f'SELECT * FROM {table}')
      data[table] = [dict(r) for r in rows]
    dump = {'schema': schema, 'data': data}
    ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'{prefix}_{ts}.json'
    with open(filename, 'w') as f:
      json.dump(dump, f, indent=2, default=str)
    print(f'Data dumped to {filename}')
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
