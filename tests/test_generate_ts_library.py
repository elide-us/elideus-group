from scripts import generate_ts_library as gen
from pydantic import BaseModel

def test_model_to_ts_simple():
  class Sample(BaseModel):
    name: str
    age: int
    active: bool
    pi: float

  ts = gen.model_to_ts(Sample)
  assert 'export interface Sample' in ts
  assert 'name: string;' in ts
  assert 'age: number;' in ts
  assert 'active: boolean;' in ts
  assert 'pi: number;' in ts


from scripts import generate_user_context as ugen


def test_generate_user_context():
 ts = ugen.generate_user_context()
 assert 'export interface UserData' in ts
 assert 'export interface UserContext' in ts
 assert 'createContext<UserContext>' in ts
