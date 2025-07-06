import os, sys
from pydantic import BaseModel

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

from scripts import generate_rpc_library as rpcgen
from scripts import generate_user_context as ctxgen

def test_model_to_ts_simple():
    class Sample(BaseModel):
        name: str
        age: int
        active: bool
        pi: float

    ts = rpcgen.model_to_ts(Sample)
    assert 'export interface Sample' in ts
    assert 'name: string;' in ts
    assert 'age: number;' in ts
    assert 'active: boolean;' in ts
    assert 'pi: number;' in ts

def test_generate_user_context():
    ts = ctxgen.generate_user_context()
    assert 'export interface UserData' in ts
    assert 'export interface UserContext' in ts or 'export interface UserContextType' in ts
    assert 'createContext<UserContext' in ts or 'createContext<UserContextType' in ts

def test_main_writes_rpc_models(tmp_path, monkeypatch):
    monkeypatch.setattr(rpcgen, 'FRONTEND_SRC', str(tmp_path))
    rpcgen.main()
    assert (tmp_path / 'RpcModels.tsx').exists()

def test_main_writes_user_context(tmp_path, monkeypatch):
    monkeypatch.setattr(ctxgen, 'FRONTEND_SRC', str(tmp_path))
    ctxgen.main()
    assert (tmp_path / 'UserContext.tsx').exists()
