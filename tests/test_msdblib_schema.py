import json
import asyncio
import pathlib

import pytest

import scripts.msdblib as msdb


class DummyConn:
  def cursor(self):
    class C:
      async def __aenter__(self):
        return self
      async def __aexit__(self, *exc):
        return False
      async def execute(self, *args, **kwargs):
        pass
      async def fetchone(self):
        return (json.dumps([]),)
    return C()


def test_dump_schema_includes_extra_fields(monkeypatch, tmp_path):
  async def fake_list_tables(conn):
    return [{'table_name': 't1'}]

  async def fake_table_schema(conn, table):
    return {
      'name': table,
      'columns': [],
      'primary_key': [],
      'foreign_keys': [],
      'indexes': [{'indexname': 'i1', 'indexdef': 'def'}],
      'keys': [{'constraint_name': 'k1', 'column_name': 'c1', 'constraint_type': 'PRIMARY KEY'}],
      'constraints': [{'constraint_name': 'k1', 'constraint_type': 'PRIMARY KEY'}],
    }

  monkeypatch.setattr(msdb, 'list_tables', fake_list_tables)
  monkeypatch.setattr(msdb, '_table_schema', fake_table_schema)

  out_prefix = str(tmp_path / 'schema')
  path = asyncio.run(msdb.dump_schema(DummyConn(), prefix=out_prefix))

  with open(path) as f:
    data = json.load(f)

  table = data['tables'][0]
  assert 'indexes' in table
  assert 'keys' in table
  assert 'constraints' in table
