from __future__ import annotations
import os, sys

from genlib import model_to_ts

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from rpc.models import UserData

FRONTEND_SRC = os.path.join(REPO_ROOT, "frontend", "src")

def generate_user_context() -> str:
    content: list[str] = ["import { createContext } from 'react';", ""]

    # ✅ Step 1: Generate UserData from Pydantic
    content.append(model_to_ts(UserData).strip())

    # ✅ Step 2: Manually write the correct React-facing UserContext interface
    content.append('export interface UserContext {')
    content.append('  userData: UserData | null;')
    content.append('  setUserData: (data: UserData | null) => void;')
    content.append('  clearUserData: () => void;')
    content.append('}')

    # ✅ Step 3: Default context object
    content.append('const defaultContext: UserContext = {')
    content.append('  userData: null,')
    content.append('  setUserData: () => {},')
    content.append('  clearUserData: () => {},')
    content.append('};')

    # ✅ Step 4: Create context object
    content.append('')
    content.append('const UserContextObject = createContext<UserContext>(defaultContext);')
    content.append('')
    content.append('export default UserContextObject;')

    return "\n".join(content)

def main() -> None:
  out_path = os.path.join(FRONTEND_SRC, "generated_user_context.tsx")
  with open(out_path, "w") as f:
    f.write(generate_user_context())
  print(f"✅ Wrote UserContext to '{out_path}'")

if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print("❌ UserContext generation failed.")
    raise e
