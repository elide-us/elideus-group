from fastapi import APIRouter, Request, HTTPException
from models.rpc import RPCRequest, RPCResponse, AdminEnvVersion1

router = APIRouter()

@router.post("/")
async def handle_rpc_request(rpc_request: RPCRequest, request: Request) -> RPCResponse:
    if rpc_request.op == "urn:admin:env:get_version:1":
        version = request.app.state.version
        payload = AdminEnvVersion1(version=version)
        return RPCResponse(op="urn:admin:env:version:1", payload=payload, version=1)
    raise HTTPException(status_code=404, detail="Unknown RPC operation")
