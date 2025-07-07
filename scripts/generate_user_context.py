from __future__ import annotations
import os

from genlib import REPO_ROOT, HEADER_COMMENT

FRONTEND_SRC = os.path.join(REPO_ROOT, "frontend", "src", "shared")

def generate_user_context() -> str:
    content: list[str] = HEADER_COMMENT + ["import { createContext } from 'react';", "import type { UserData } from './RpcModels';", ""]

    # UserData interface is defined in RpcModels.tsx

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

def main(output_dir: str = FRONTEND_SRC) -> None:
  os.makedirs(output_dir, exist_ok=True)
  out_path = os.path.join(output_dir, "UserContext.tsx")
  with open(out_path, "w") as f:
    f.write(generate_user_context())
  print(f"✅ Wrote UserContext to '{out_path}'")

if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print("❌ UserContext generation failed.")
    raise e
