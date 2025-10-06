import logging

from fastapi import HTTPException, Request

from rpc import HANDLERS
from rpc.helpers import unbox_request
from server.errors import (
  RPCServiceError,
  as_http_exception,
  bad_request,
  from_http_exception,
  not_found,
)
from server.helpers.context import get_request_id, request_id_context
from server.models import RPCResponse


_logger = logging.getLogger(__name__)


async def handle_rpc_request(request: Request) -> RPCResponse:
  rpc_request, _, parts = await unbox_request(request)
  with request_id_context(rpc_request.request_id):
    _logger.info(
      "[RPC %s] Received request for %s", rpc_request.request_id, rpc_request.op,
    )
    return await _dispatch_rpc_request(request, rpc_request, parts)


async def _dispatch_rpc_request(request, rpc_request, parts: list[str]) -> RPCResponse:
  request_id = get_request_id()
  try:
    if parts[:1] != ['urn']:
      raise bad_request('Invalid URN prefix', diagnostic=f'Parts={parts}')
    domain = parts[1]
    remainder = parts[2:]
    handler = HANDLERS.get(domain)
    if not handler:
      raise not_found('Unknown RPC domain', diagnostic=f'Domain={domain}')
    _logger.debug("[RPC %s] Dispatching domain handler %s", request_id, domain)
    response = await handler(remainder, request)
    _logger.info("[RPC %s] RPC completed: %s", request_id, rpc_request.op)
    return response
  except RPCServiceError as exc:
    _logger.error(
      "[RPC %s] RPC failed: %s (%s)",
      request_id,
      rpc_request.op,
      exc.detail.diagnostic,
    )
    raise as_http_exception(exc) from exc
  except HTTPException as exc:
    wrapped = from_http_exception(exc)
    _logger.error(
      "[RPC %s] RPC failed: %s (%s)",
      request_id,
      rpc_request.op,
      wrapped.detail.diagnostic,
    )
    raise as_http_exception(wrapped) from exc
  except Exception:
    _logger.exception("[RPC %s] RPC failed: %s", request_id, rpc_request.op)
    raise
