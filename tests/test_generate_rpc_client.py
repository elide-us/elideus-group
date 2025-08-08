import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from generate_rpc_client import parse_dispatchers, parse_service_models


def test_parse_dispatchers():
  path = 'rpc/auth/microsoft/__init__.py'
  base, ops = parse_dispatchers(path)
  assert base == ['auth', 'microsoft']
  assert ops == [{
    'op': 'oauth_login',
    'version': '1',
    'func': 'auth_microsoft_oauth_login_v1'
  }]


def test_parse_service_models_no_payload():
  path = 'rpc/auth/microsoft/services.py'
  models = parse_service_models(path)
  assert models == {}

