from __future__ import annotations
import logging
from typing import Callable, Dict, Optional, TYPE_CHECKING
from fastapi import FastAPI
from . import BaseModule

if TYPE_CHECKING:
  from rpc.models import RPCResponse

FormatFunc = Callable[["RPCResponse"], "RPCResponse"]

# Global registry mapping base RPC op -> context -> variant -> formatter
VIEW_REGISTRY: Dict[str, Dict[str, Dict[str, FormatFunc]]] = {}


class ViewsModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    logging.info("Views module loaded")


def register_formatter(op: str, context: str, variant: Optional[str] = None):
  def decorator(func: FormatFunc) -> FormatFunc:
    ctx_map = VIEW_REGISTRY.setdefault(op, {}).setdefault(context, {})
    ctx_map[str(variant or "")] = func
    return func
  return decorator


def format_response(response: RPCResponse, context: Optional[str], variant: Optional[str]) -> RPCResponse:
  if not context:
    return response
  ctx_map = VIEW_REGISTRY.get(response.op, {})
  var_map = ctx_map.get(context, {})
  fmt = var_map.get(str(variant or "")) or var_map.get("")
  if fmt:
    return fmt(response)
  return response


def get_view_registry() -> Dict[str, Dict[str, list[str]]]:
  return {
    op: {ctx: list(vars.keys()) for ctx, vars in ctxs.items()}
    for op, ctxs in VIEW_REGISTRY.items()
  }
