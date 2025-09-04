import asyncio
from pathlib import Path
import scripts.msdblib as mlib

async def fake_get_schema(conn):
  return {
    'tables': [{
      'name': 't1',
      'columns': [{
        'name': 'id', 'type': 'int', 'length': None,
        'nullable': False, 'default': None
      }],
      'primary_key': [],
      'foreign_keys': [],
      'indexes': []
    }],
    'views': [{
      'name': 'v_t1',
      'definition': 'CREATE VIEW v_t1 AS SELECT id FROM t1'
    }]
  }

def test_dump_schema_includes_views(tmp_path, monkeypatch):
  monkeypatch.setattr(mlib, 'get_schema', fake_get_schema)
  filename = asyncio.run(mlib.dump_schema(None, prefix=str(tmp_path / 'schema')))
  text = Path(filename).read_text()
  assert 'CREATE VIEW v_t1 AS SELECT id FROM t1;' in text
