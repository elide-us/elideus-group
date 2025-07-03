from fastapi import Request
from rpc.admin.vars.models import AdminVarsVersion1, AdminVarsHostname1
from rpc.models import RPCResponse

async def get_version_v1(request: Request):
  version = request.app.state.version
  payload = AdminVarsVersion1(version=version)
  return RPCResponse(op="urn:admin:vars:version:1", payload=payload, version=1)

async def get_hostname_v1(request: Request):
  hostname = request.app.state.hostname
  payload = AdminVarsHostname1(hostname=hostname)
  return RPCResponse(op="urn:admin:vars:hostname:1", payload=payload, version=1)