from __future__ import annotations
import os
from scripts.generate_ts_library import model_to_ts
from rpc.models import UserData, UserContext

REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')
FRONTEND_SRC = os.path.join(REPO_ROOT, 'frontend', 'src')


def generate_user_context() -> str:
 content: list[str] = ['import { createContext } from \"react\";', '']
 content.append(model_to_ts(UserData).strip())
 content.append(model_to_ts(UserContext).strip())
 content.append('const defaultContext: UserContext = {')
 content.append(' userData: null,')
 content.append('};')
 content.append('')
 content.append('const UserContextObject = createContext<UserContext>(defaultContext);')
 content.append('')
 content.append('export default UserContextObject;')
 return "\n".join(content)


def main() -> None:
 out_path = os.path.join(FRONTEND_SRC, 'generated_user_context.tsx')
 with open(out_path, 'w') as f:
  f.write(generate_user_context())
 print(f"✅ Wrote UserContext to '{out_path}'")


if __name__ == '__main__':
 main()
