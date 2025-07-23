from __future__ import annotations
from typing import Callable, Dict, List, Tuple
from fastapi import HTTPException
from rpc.models import RPCResponse

SuffixHandler = Callable[[RPCResponse, List[str]], RPCResponse]

class SuffixSpec:
  def __init__(self, arg_count: int, handler: SuffixHandler):
    self.arg_count = arg_count
    self.handler = handler

SUFFIX_REGISTRY: Dict[str, SuffixSpec] = {}


def register_suffix(name: str, arg_count: int):
  def decorator(func: SuffixHandler) -> SuffixHandler:
    SUFFIX_REGISTRY[name] = SuffixSpec(arg_count, func)
    return func
  return decorator


def split_suffix(parts: List[str]) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
  core: List[str] = []
  suffix_tokens: List[str] = []
  found = False
  for i, part in enumerate(parts):
    if part in SUFFIX_REGISTRY:
      core = parts[:i]
      suffix_tokens = parts[i:]
      found = True
      break
  if not found:
    return parts, []

  suffixes: List[Tuple[str, List[str]]] = []
  idx = 0
  while idx < len(suffix_tokens):
    name = suffix_tokens[idx]
    spec = SUFFIX_REGISTRY.get(name)
    if not spec:
      raise HTTPException(400, f"Unknown suffix: {name}")
    args = suffix_tokens[idx + 1: idx + 1 + spec.arg_count]
    if len(args) < spec.arg_count:
      raise HTTPException(400, f"Invalid suffix parameters for {name}")
    suffixes.append((name, args))
    idx += 1 + spec.arg_count
  return core, suffixes


def encode_suffixes(suffixes: List[Tuple[str, List[str]]]) -> List[str]:
  parts: List[str] = []
  for name, args in suffixes:
    parts.append(name)
    parts.extend(args)
  return parts


def apply_suffixes(response: RPCResponse, suffixes: List[Tuple[str, List[str]]], request_op: str) -> RPCResponse:
  has_view = any(name == "view" for name, _ in suffixes)
  if not has_view:
    suffixes = suffixes + [("view", ["default", "1"])]

  for name, args in suffixes:
    spec = SUFFIX_REGISTRY.get(name)
    if spec:
      response = spec.handler(response, args)

  if has_view:
    response.op = request_op
  else:
    response.op = f"{response.op}:" + ":".join(encode_suffixes([("view", ["default", "1"])]))
  return response

# @register_suffix("example", 2)
# def _example_handler(resp: RPCResponse, args: List[str]) -> RPCResponse:
#   from rpc.example.namespace.models import ExampleSuffix1
#   example, version = args
#   if resp.op == "urn:example:namespace:operation:1" and example == "example" and version == "1":
#     assert isinstance(resp.payload, ExampleSuffix1)
#     resp.payload = ExampleSuffix1(content=f"Example: {resp.payload.example}")
#   return resp

@register_suffix("view", 2)
def _view_handler(resp: RPCResponse, args: List[str]) -> RPCResponse:
  from rpc.frontend.vars.models import ViewDiscord1
  context, version = args
  if resp.op == "urn:frontend:vars:hostname:1" and context == "discord" and version == "1":
    from rpc.frontend.vars.models import FrontendVarsHostname1
    assert isinstance(resp.payload, FrontendVarsHostname1)
    resp.payload = ViewDiscord1(content=f"Hostname: {resp.payload.hostname}")
  if resp.op == "urn:frontend:vars:version:1" and context == "discord" and version == "1":
    from rpc.frontend.vars.models import FrontendVarsVersion1
    assert isinstance(resp.payload, FrontendVarsVersion1)
    resp.payload = ViewDiscord1(content=f"Version: {resp.payload.version}")
  if resp.op == "urn:frontend:vars:repo:1" and context == "discord" and version == "1":
    from rpc.frontend.vars.models import FrontendVarsRepo1
    assert isinstance(resp.payload, FrontendVarsRepo1)
    resp.payload = ViewDiscord1(content=f"GitHub: {resp.payload.repo}")
  return resp

