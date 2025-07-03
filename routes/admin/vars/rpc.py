from typing import List
from fastapi import Request, HTTPException
from models.rpc import RPCResponse
from models.admin.vars.rpc import AdminVarsVersion1, AdminVarsHostname1

async def handle_vars_request(urn: List, request: Request):
  match urn[1:]:
    case ["get_version", "1"]:
      version = request.app.state.version
      payload = AdminVarsVersion1(version=version)
      return RPCResponse(op="urn:admin:vars:version:1", payload=payload, version=1)
    case ["get_hostname", "1"]:
      hostname = request.app.state.hostname
      payload = AdminVarsHostname1(hostname=hostname)
      return RPCResponse(op="urn:admin:vars:hostname:1", payload=payload, version=1)
    case _:
      raise HTTPException(status_code=404, detail="Unknown RPC operation")
