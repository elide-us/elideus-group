
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
  "export async function rpcCall<T>(op: string, payload: any = null): Promise<T> {",
  "    const request: RPCRequest = {",
  "        op,",
  "        payload,",
  "        version: 1,",
  "        timestamp: new Date().toISOString(),",
  "        user_guid: null,",
  "        roles: [],",
  "        role_mask: 0",
  "    };",
  "    const headers: Record<string, string> = {};",
  "    if (typeof localStorage !== 'undefined') {",
  "        try {",
  "            const raw = localStorage.getItem('authTokens');",
  "            if (raw) {",
  "                const { sessionToken } = JSON.parse(raw);",
  "                if (sessionToken) headers.Authorization = `Bearer ${sessionToken}`;",
  "            }",
  "        } catch {",
  "            /* ignore token parsing errors */",
  "        }",
  "    }",
  "    try {",
  "        const response = await axios.post<RPCResponse>('/rpc', request, { headers });",
  "        return response.data.payload as T;",
  "    } catch (err: any) {",
  "        if (axios.isAxiosError(err) && err.response?.status === 401) {",
  "            if (typeof localStorage !== 'undefined') {",
  "                localStorage.removeItem('authTokens');",
  "            }",
  "            if (typeof window !== 'undefined') {",
  "                window.dispatchEvent(new Event('sessionExpired'));",
  "            }",
  "        }",
  "        throw err;",
  "    }",
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
