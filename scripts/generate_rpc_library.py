
from __future__ import annotations
import os
import inspect
from typing import List
from pydantic import BaseModel
from genlib import REPO_ROOT, HEADER_COMMENT, load_module, model_to_ts

RPC_CALL_FUNC = [
  "export async function rpcCall<T>(op: string, payload: any = null): Promise<T> {",
  "    const request: RPCRequest = {",
  "        op,",
  "        payload,",
  "        version: 1,",
  "        timestamp: Date.now(),",
  "        metadata: null,",
  "    };",
  "    const response = await axios.post<RPCResponse>('/rpc', request);",
  "    return response.data.payload as T;",
  "}",
]

ROOT = os.path.join(REPO_ROOT, 'rpc')
FRONTEND_SRC = os.path.join(REPO_ROOT, 'frontend', 'src', 'shared')


def extract_interfaces_from_models_py(path: str) -> List[str]:
  interfaces = []
  module = load_module(path)
  for _, obj in inspect.getmembers(module):
    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel:
      print(f"🧩 Found model: {obj.__name__}")
      interfaces.append(model_to_ts(obj))
  return interfaces

def find_all_interfaces() -> List[str]:
  interfaces = []
  for root, _, files in os.walk(ROOT):
    if 'models.py' in files:
      models_path = os.path.join(root, 'models.py')
      interfaces.extend(extract_interfaces_from_models_py(models_path))
  return interfaces

def write_interfaces_to_file(interfaces: List[str], output_dir: str) -> None:
  os.makedirs(output_dir, exist_ok=True)
  out_path = os.path.join(output_dir, 'RpcModels.tsx')
  with open(out_path, 'w') as f:
    lines = HEADER_COMMENT + ['import axios from \"axios\";', '']
    lines += interfaces + [''] + RPC_CALL_FUNC + ['']
    f.write("\n".join(lines))
  print(f"✅ Wrote {len(interfaces)} TypeScript interfaces to '{out_path}'")


def main(output_dir: str = FRONTEND_SRC) -> None:
  print("✨ Starting RPC model extraction and TS generation...")
  interfaces = find_all_interfaces()
  write_interfaces_to_file(interfaces, output_dir)


if __name__ == "__main__":
  main()
