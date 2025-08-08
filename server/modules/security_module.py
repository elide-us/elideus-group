import json, os, logging
from pathlib import Path
from fastapi import FastAPI
from . import BaseModule

class SecurityModule(BaseModule):
  def __init__(self, app: FastAPI, metadata_file: str | None = None):
    super().__init__(app)
    root = Path(__file__).resolve().parents[1]
    self.metadata_file = metadata_file or os.path.join(root, 'rpc', 'metadata.json')
    self.capabilities: dict[str, int] = {}

  async def startup(self):
    await self.load()
    logging.info("PermCapModule loaded %d capability ops", len(self.capabilities))
    self.mark_ready()

  async def shutdown(self):
    logging.info("PermCapModule shutdown")

  async def load(self):
    try:
      with open(self.metadata_file, 'r') as f:
        data = json.load(f)
      self.capabilities = {
        i['op']: i.get('capabilities', 0)
        for i in data.get('rpc', [])
        if 'op' in i
      }
    except FileNotFoundError:
      logging.warning("PermCapModule metadata file not found: %s", self.metadata_file)
      self.capabilities = {}
    except Exception as e:
      logging.error("PermCapModule failed to load capabilities: %s", e)
      self.capabilities = {}

  def get_capabilities(self, op: str) -> int:
    return self.capabilities.get(op, 0)

  def filter_routes(self, routes: list[dict], role_mask: int) -> list[dict]:
    allowed: list[dict] = []
    for r in routes:
      req_mask = r.get('required_roles') or r.get('element_roles') or 0
      if req_mask == 0 or req_mask & role_mask == req_mask:
        allowed.append(r)
    return allowed

