
from __future__ import annotations
import os
import sys
import inspect
from typing import List
from pydantic import BaseModel
from genlib import REPO_ROOT, HEADER_COMMENT, load_module, model_to_ts

# Ensure repo root is on sys.path so RPC modules can be imported with package names
sys.path.insert(0, REPO_ROOT)

RPC_CALL_FUNC = [
  "export async function rpcCall<T>(op: string, payload: any = null, user_guid: string, user_role: number): Promise<T> {",
  "    const request: RPCRequest = {",
  "        op,",
  "        payload,",
  "        user_guid,",
  "        user_role,",
  "        version: 1,",
  "        timestamp: new Date().toISOString()",
  "    };",
  "    const headers: Record<string, string> = {};",
  "    if (typeof localStorage !== 'undefined') {",
  "        try {",
  "            const raw = localStorage.getItem('authTokens');",
  "            if (raw) {",
  "                const { bearerToken } = JSON.parse(raw);",
  "                if (bearerToken) headers.Authorization = `Bearer ${bearerToken}`;",
  "            }",
  "        } catch {",
  "            /* ignore token parsing errors */",
  "        }",
  "    }",
  "    const response = await axios.post<RPCResponse>('/rpc', request, { headers });",
  "    return response.data.payload as T;",
  "}",
]

ROOT = os.path.join(REPO_ROOT, 'rpc')
FRONTEND_SRC = os.path.join(REPO_ROOT, 'frontend', 'src', 'shared')


def extract_interfaces_from_models_py(path: str, seen: set[str]) -> List[str]:
  interfaces = []
  try:
    module = load_module(path)
  except Exception as e:
    print(f"⚠️ Skipping '{path}' due to import error: {e}")
    return interfaces

  for _, obj in inspect.getmembers(module):
    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel:
      if obj.__name__ in seen:
        continue
      print(f"🧩 Found model: {obj.__name__}")
      seen.add(obj.__name__)
      interfaces.append(model_to_ts(obj))

  return interfaces


def find_all_interfaces() -> List[str]:
  interfaces = []
  seen: set[str] = set()
  for root, _, files in os.walk(ROOT):
    if 'models.py' in files:
      models_path = os.path.join(root, 'models.py')
      interfaces.extend(extract_interfaces_from_models_py(models_path, seen))
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
