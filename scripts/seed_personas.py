import asyncio, json
from pathlib import Path
from scriptlib import connect

DEFAULT_JSON = Path(__file__).resolve().parent / 'data' / 'assistant_personas.json'

async def seed_personas(json_path: Path) -> None:
  with json_path.open() as f:
    personas = json.load(f)
  conn = await connect()
  try:
    async with conn.cursor() as cur:
      for p in personas:
        meta = json.dumps({
          'model': p['model'],
          'max_tokens': p['max_tokens'],
          'role': p['role']
        })
        await cur.execute(
          'INSERT INTO assistant_personas (element_name, element_metadata) VALUES (?, ?);',
          (p['name'], meta)
        )
  finally:
    await conn.close()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Seed assistant personas from JSON')
  parser.add_argument('json', nargs='?', default=DEFAULT_JSON, type=Path)
  args = parser.parse_args()
  asyncio.run(seed_personas(args.json))
