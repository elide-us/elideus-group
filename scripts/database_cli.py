from __future__ import annotations
import os, json, asyncio, asyncpg, dotenv

dotenv.load_dotenv()

HELP_TEXT = """
Available commands:
  help                               Show this help message
  exit, quit                         Exit the console
  reconnect <db>                     Connect to a different database
  list tables                        List all tables
  list columns <table>               List columns of a table
  list indexes <table>               List indexes on a table
  index all                          Reindex the current database
  get public                         Write template data to public_templates.json
  get layer <id>                     Write a key layer to data_layer<ID>.json
  get keys                           Show distinct key/layer values
  parse templates                    Load template JSON into the database
  parse data                         Load base key data from files
  parse private                      Load private key data from the data folder
  parse assistants                   Insert assistant definitions
"""

async def list_tables(conn):
  query = """
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public';
  """
  return await conn.fetch(query)

async def list_columns(conn, table):
  query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name=$1;
  """
  return await conn.fetch(query, table)

async def list_indexes(conn, table):
  query = """
    SELECT indexname, indexdef
    FROM pg_indexes WHERE tablename=$1;
  """
  return await conn.fetch(query, table)

async def get_public(conn):
  query = """
    WITH template_data AS (
      SELECT c.name AS category,
        json_agg(json_build_object(
          'title', t.title,
          'description', t.description,
          'imageUrl', t.image_url,
          'layer1', t.layer1,
          'layer2', t.layer2,
          'layer3', t.layer3,
          'layer4', t.layer4,
          'input', t.input
        )) AS templates
      FROM templates t
      JOIN categories c ON t.category_id=c.id
      GROUP BY c.name
    )
    SELECT json_object_agg(category, templates) AS result
    FROM template_data;
  """
  result = await conn.fetchval(query)
  with open('public_templates.json', 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
  return result

async def get_layer(conn, layer):
  query = """
    SELECT jsonb_object_agg(key_value, subkeys) AS layer_data
    FROM (
      SELECT key_value,
        jsonb_object_agg(subkey_value, public_value) AS subkeys
      FROM keys WHERE layer=$1 GROUP BY key_value
    ) AS grouped;
  """
  result = await conn.fetchval(query, layer)
  data = json.loads(result)
  with open(f'data_layer{layer}.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  return data

async def connect(dbname=None):
  dsn = os.getenv('POSTGRES_CONNECTION_STRING')
  if not dsn:
    raise RuntimeError('POSTGRES_CONNECTION_STRING not set')
  if dbname:
    parts = dsn.rsplit('/', 1)
    dsn = '/'.join([parts[0], dbname])
  conn = await asyncpg.connect(dsn=dsn)
  print(f'Connected to database {dbname or dsn.rsplit("/",1)[1]}.')
  return conn

async def interactive_console(conn):
  print("Type 'help' for commands. Type 'exit' to quit.")
  while True:
    raw = input('SQL> ').strip()
    if not raw:
      continue
    cmd = raw.split()
    match cmd:
      case ['quit'] | ['exit']:
        break
      case ['help']:
        print(HELP_TEXT)
      case ['reconnect', db]:
        try:
          await conn.close()
          conn = await connect(db)
        except Exception as e:
          print(f'Error reconnecting: {e}')
      case ['list', 'tables']:
        rows = await list_tables(conn)
        for r in rows:
          print(r['table_name'])
      case ['list', 'columns', table]:
        rows = await list_columns(conn, table)
        for r in rows:
          print(f"{r['column_name']} ({r['data_type']})")
      case ['list', 'indexes', table]:
        rows = await list_indexes(conn, table)
        for r in rows:
          print(f"{r['indexname']} ({r['indexdef']})")
      case ['index', 'all']:
        await conn.execute('REINDEX DATABASE current_database()')
        print('Reindex complete.')
      case ['get', 'public']:
        print(await get_public(conn))
      case ['get', 'layer', lid]:
        try:
          lid_int = int(lid)
        except ValueError:
          print('Layer id must be an integer')
          continue
        print(await get_layer(conn, lid_int))
      case ['get', 'keys']:
        rows = await conn.fetch('SELECT DISTINCT key_value, layer FROM keys ORDER BY layer, key_value')
        for r in rows:
          print(dict(r))
      case ['parse', 'templates']:
        if not os.path.exists('templates.json'):
          print('templates.json not found')
          continue
        with open('templates.json', 'r') as f:
          data = json.load(f)
        for cat, templates in data.items():
          for t in templates:
            q = """
              INSERT INTO templates (category, title, description, image_url, layer1, layer2, layer3, layer4, input)
              VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9);
            """
            vals = [cat, t['title'], t['description'], t['imageUrl'], t['layer1'], t['layer2'], t['layer3'], t['layer4'], t['input']]
            await conn.execute(q, *vals)
        print('Templates inserted.')
      case ['parse', 'data']:
        for layer in range(1,5):
          fname = f'data_layer{layer}.json'
          if not os.path.exists(fname):
            print(f'{fname} not found')
            continue
          with open(fname, 'r') as f:
            data = json.load(f)
          q = """
            INSERT INTO keys (layer, key_value, subkey_value, public_value)
            VALUES ($1,$2,$3,$4);
          """
          async with conn.transaction():
            for k, sub in data.items():
              if isinstance(sub, dict):
                for sk, val in sub.items():
                  await conn.execute(q, layer, k, sk, val)
        print('Base key data inserted.')
      case ['parse', 'private']:
        for fname in os.listdir('data'):
          if fname.endswith('.json'):
            key_val = fname[:-5]
            path = f'data/{fname}'
            with open(path, 'r') as f:
              data = json.load(f)
            q = """
              UPDATE keys SET private_value=$1 WHERE key_value=$2 AND subkey_value=$3;
            """
            async with conn.transaction():
              for sk, detail in data.items():
                if 'private' in detail:
                  await conn.execute(q, detail['private'], key_val, sk)
        print('Private values updated.')
      case ['parse', 'assistants']:
        if not os.path.exists('data_assistants.json'):
          print('data_assistants.json not found')
          continue
        with open('data_assistants.json', 'r') as f:
          data = json.load(f)
        for name, val in data.items():
          await conn.execute(
            'INSERT INTO assistants(name, model, max_tokens, role) VALUES($1,$2,$3,$4)',
            name, val['model'], val['max_tokens'], val['role']
          )
        print('Assistants inserted.')
      case _:
        try:
          rows = await conn.fetch(raw)
          for r in rows:
            print(dict(r))
        except Exception as e:
          try:
            result = await conn.execute(raw)
            print(result)
          except Exception as e2:
            print(f'Error: {e2}')

async def main():
  conn = await connect()
  try:
    await interactive_console(conn)
  finally:
    await conn.close()

if __name__ == '__main__':
  asyncio.run(main())
