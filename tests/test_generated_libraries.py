import os, sys
from pydantic import BaseModel

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

from scripts import generate_rpc_library as rpcgen

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

def test_main_writes_rpc_models(tmp_path):
    rpcgen.main(output_dir=str(tmp_path))
    assert (tmp_path / 'RpcModels.tsx').exists()

from scripts import generate_rpc_client as clientgen

def test_main_writes_rpc_client(tmp_path):
  clientgen.main(output_dir=str(tmp_path))
  assert (tmp_path / 'admin' / 'vars' / 'index.ts').exists()
