
from __future__ import annotations
import os
import sys
import inspect
from typing import List
from pydantic import BaseModel
from scriptlib import REPO_ROOT, HEADER_COMMENT, load_module, model_to_ts

# Ensure repo root is on sys.path so RPC modules can be imported with package names
sys.path.insert(0, REPO_ROOT)

RPC_CALL_FUNC = [
  "export async function rpcCall<T>(op: string, payload: any = null): Promise<T> {",
  "\tconst request = {",
  "\top,",
  "\tpayload,",
  "\tversion: 1,",
  "\ttimestamp: new Date().toISOString(),",
  "\t};",
  "\tconst headers: Record<string, string> = {};",
  "\tif (typeof localStorage !== 'undefined') {",
  "\t\ttry {",
  "\t\t\tconst raw = localStorage.getItem('authTokens');",
  "\t\t\tif (raw) {",
  "\t\t\t\tconst { sessionToken } = JSON.parse(raw);",
  "\t\t\t\tif (sessionToken) headers.Authorization = `Bearer ${sessionToken}`;",
  "\t\t\t}",
  "\t\t} catch {",
  "\t\t\t/* ignore token parsing errors */",
  "\t\t}",
  "\t}",
  "\ttry {",
  "\t\tconst response = await axios.post('/rpc', request, { headers });",
  "\t\treturn response.data.payload as T;",
  "\t} catch (err: any) {",
  "\t\tif (axios.isAxiosError(err) && err.response?.status === 401) {",
  "\t\t\ttry {",
  "\t\t\t\tconst refreshReq = {",
  "\t\t\t\t\top: 'urn:auth:session:refresh_token:1',",
  "\t\t\t\t\tpayload: null,",
  "\t\t\t\t\tversion: 1,",
  "\t\t\t\t\ttimestamp: new Date().toISOString(),",
  "\t\t\t\t};",
  "\t\t\t\tconst refreshResp = await axios.post('/rpc', refreshReq);",
  "\t\t\t\tconst newToken = refreshResp.data.payload.token;",
  "\t\t\t\tif (typeof localStorage !== 'undefined') {",
  "\t\t\t\t\tconst raw = localStorage.getItem('authTokens');",
  "\t\t\t\t\tif (raw) {",
  "\t\t\t\t\t\tconst data = JSON.parse(raw);",
  "\t\t\t\t\t\tdata.sessionToken = newToken;",
  "\t\t\t\t\t\tlocalStorage.setItem('authTokens', JSON.stringify(data));",
  "\t\t\t\t\t}",
  "\t\t\t\t}",
  "\t\t\t\theaders.Authorization = `Bearer ${newToken}`;",
  "\t\t\t\tconst retryResp = await axios.post('/rpc', request, { headers });",
  "\t\t\t\treturn retryResp.data.payload as T;",
  "\t\t\t} catch {",
  "\t\t\t\tif (typeof localStorage !== 'undefined') {",
  "\t\t\t\t\tlocalStorage.removeItem('authTokens');",
  "\t\t\t\t}",
  "\t\t\t\tif (typeof window !== 'undefined') {",
  "\t\t\t\t\twindow.dispatchEvent(new Event('sessionExpired'));",
  "\t\t\t\t}",
  "\t\t\t}",
  "\t\t}",
  "\t\tthrow err;",
  "\t}",
  "}",
]


def to_tabs(text: str) -> str:
  lines = []
  for line in text.splitlines():
    leading = len(line) - len(line.lstrip(' '))
    tabs = "\t" * (leading // 2)
    lines.append(tabs + line.lstrip(' '))
  return "\n".join(lines)

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
      if obj.__name__ in {"RPCRequest", "RPCResponse"}:
        continue
      if obj.__name__ in seen:
        continue
      print(f"🧩 Found model: {obj.__name__}")
      seen.add(obj.__name__)
      interfaces.append(to_tabs(model_to_ts(obj)))

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
