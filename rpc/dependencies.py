"""Helper dependencies for RPC handlers."""

from fastapi import HTTPException, Request

from server.modules import AuthService, ModuleServices


def get_module_services(request: Request) -> ModuleServices:
  services = getattr(request.app.state, "services", None)
  if not services:
    raise HTTPException(status_code=500, detail="Service registry unavailable")
  return services


def get_auth_service(request: Request) -> AuthService:
  services = get_module_services(request)
  auth = getattr(services, "auth", None)
  if not auth:
    raise HTTPException(status_code=500, detail="Authentication service unavailable")
  return auth
