import server

def test_server_exports():
  assert 'rpc_router' in server.__all__
  assert server.rpc_router
  assert server.web_router
  assert server.lifespan

