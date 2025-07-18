from __future__ import annotations
import asyncio, dblib

SCHEMA_FILE = 'scripts/v0.1.4.0_20250718.json'

async def main() -> None:
  try:
    conn = await dblib.connect()
    try:
      await dblib.apply_schema(conn, SCHEMA_FILE)
      print(f'Schema {SCHEMA_FILE} applied successfully.')
    except Exception as e:
      print(f'Error applying schema: {e}')
    finally:
      await conn.close()
  except Exception as e:
    print(f'Error connecting to database: {e}')

if __name__ == '__main__':
  asyncio.run(main())
