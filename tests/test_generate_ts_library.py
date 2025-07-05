import tempfile
from textwrap import dedent
from types import ModuleType

from scripts import generate_ts_library as gen
from pydantic import BaseModel


def test_model_to_ts_simple():
    class Sample(BaseModel):
        name: str
        age: int

    ts = gen.model_to_ts(Sample)
    assert 'export interface Sample' in ts
    assert 'name: string;' in ts
    assert 'age: number;' in ts

