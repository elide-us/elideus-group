"""Service functions for service.rpcdispatch RPC operations."""

from __future__ import annotations

from fastapi import Request

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
  result: ServiceRpcdispatchDomainList1 = await module.list_domains()
  domains = [ServiceRpcdispatchDomainItem1(**row) for row in result]
  payload = ServiceRpcdispatchDomainList1(domains=domains)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_subdomains_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  result: ServiceRpcdispatchSubdomainList1 = await module.list_subdomains()
  subdomains = [ServiceRpcdispatchSubdomainItem1(**row) for row in result]
  payload = ServiceRpcdispatchSubdomainList1(subdomains=subdomains)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_functions_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  result: ServiceRpcdispatchFunctionList1 = await module.list_functions()
  functions = [ServiceRpcdispatchFunctionItem1(**row) for row in result]
  payload = ServiceRpcdispatchFunctionList1(functions=functions)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_models_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  result: ServiceRpcdispatchModelList1 = await module.list_models()
  models = [ServiceRpcdispatchModelItem1(**row) for row in result]
  payload = ServiceRpcdispatchModelList1(models=models)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)


async def service_rpcdispatch_list_model_fields_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module = request.app.state.rpcdispatch
  await module.on_ready()
  result: ServiceRpcdispatchModelFieldList1 = await module.list_model_fields()
  fields = [ServiceRpcdispatchModelFieldItem1(**row) for row in result]
  payload = ServiceRpcdispatchModelFieldList1(fields=fields)
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
