import sys, importlib.util, pathlib, types, pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

@pytest.fixture(autouse=True)
def restore_rpc_helpers():
  spec = importlib.util.spec_from_file_location('rpc.helpers', ROOT / 'rpc/helpers.py')
  real = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(real)
  sys.modules.setdefault('rpc', types.ModuleType('rpc'))
  yield
  sys.modules['rpc.helpers'] = real
