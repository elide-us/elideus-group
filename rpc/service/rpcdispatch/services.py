"""Service functions for service.rpcdispatch RPC operations."""

from __future__ import annotations

from fastapi import Request

from queryregistry.rpcdispatch.domains import list_domains_request
from queryregistry.rpcdispatch.functions import list_functions_request
from queryregistry.rpcdispatch.model_fields import list_model_fields_request
from queryregistry.rpcdispatch.models import list_models_request
from queryregistry.rpcdispatch.subdomains import list_subdomains_request
from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import (
  ServiceRpcdispatchDomainItem1,
  ServiceRpcdispatchDomainList1,
  ServiceRpcdispatchFunctionItem1,
  ServiceRpcdispatchFunctionList1,
  ServiceRpcdispatchModelFieldItem1,
  ServiceRpcdispatchModelFieldList1,
  ServiceRpcdispatchModelItem1,
  ServiceRpcdispatchModelList1,
  ServiceRpcdispatchSubdomainItem1,
  ServiceRpcdispatchSubdomainList1,
)


async def service_rpcdispatch_list_domains_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  db = request.app.state.db
  await db.on_ready()
  result = await db.run(list_domains_request())
  domains = [ServiceRpcdispatchDomainItem1(**row) for row in (result.rows or [])]
  payload = ServiceRpcdispatchDomainList1(domains=domains)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_subdomains_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  db = request.app.state.db
  await db.on_ready()
  result = await db.run(list_subdomains_request())
  subdomains = [ServiceRpcdispatchSubdomainItem1(**row) for row in (result.rows or [])]
  payload = ServiceRpcdispatchSubdomainList1(subdomains=subdomains)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_functions_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  db = request.app.state.db
  await db.on_ready()
  result = await db.run(list_functions_request())
  functions = [ServiceRpcdispatchFunctionItem1(**row) for row in (result.rows or [])]
  payload = ServiceRpcdispatchFunctionList1(functions=functions)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_models_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  db = request.app.state.db
  await db.on_ready()
  result = await db.run(list_models_request())
  models = [ServiceRpcdispatchModelItem1(**row) for row in (result.rows or [])]
  payload = ServiceRpcdispatchModelList1(models=models)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_model_fields_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  db = request.app.state.db
  await db.on_ready()
  result = await db.run(list_model_fields_request())
  fields = [ServiceRpcdispatchModelFieldItem1(**row) for row in (result.rows or [])]
  payload = ServiceRpcdispatchModelFieldList1(fields=fields)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
