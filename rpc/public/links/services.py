from fastapi import Request
import importlib.util
import pathlib
import sys

# The admin service tests monkeypatch ``rpc.helpers`` with a stub module and do
# not restore it afterwards.  Subsequent tests that import helper functions (the
# public link and vars services as well as ``tests/test_rpc_helpers.py``) expect
# the real implementation.  To ensure the helpers are available we reload the
# helper module directly from the source file and replace the entry in
# ``sys.modules``.  This makes the import resilient to earlier stubs while still
# allowing tests to monkeypatch the function attribute as needed.
_helpers_spec = importlib.util.spec_from_file_location(
  "rpc.helpers", pathlib.Path(__file__).resolve().parents[2] / "helpers.py"
)
_helpers_mod = importlib.util.module_from_spec(_helpers_spec)
_helpers_spec.loader.exec_module(_helpers_mod)
sys.modules["rpc.helpers"] = _helpers_mod
unbox_request = _helpers_mod.unbox_request

from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  PublicLinksHomeLinks1,
  PublicLinksLinkItem1,
  PublicLinksNavBarRoute1,
  PublicLinksNavBarRoutes1,
)


async def public_links_get_home_links_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, rpc_request.payload or {})
  links = [PublicLinksLinkItem1(**row) for row in res.rows]
  payload = PublicLinksHomeLinks1(links=links)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_links_get_navbar_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  db: DbModule = request.app.state.db
  res = await db.run("urn:public:links:get_navbar_routes:1", {"role_mask": auth_ctx.role_mask})
  routes = [PublicLinksNavBarRoute1(**row) for row in res.rows]
  payload = PublicLinksNavBarRoutes1(routes=routes)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

