# database_module.py
from typing import Any, Dict
from pydantic import BaseModel

class DBResult(BaseModel):
    rows: list[dict] = []
    rowcount: int = 0

_exec = None  # set by init()

async def init(provider: str = "mssql", **cfg):
    global _exec
    if provider == "mssql":
        from .providers.mssql_provider import init as _init, dispatch as _dispatch
        await _init(**cfg)
        _exec = _dispatch
    elif provider == "postgres":
        from .providers.postgres_provider import init as _init, dispatch as _dispatch
        await _init(**cfg)
        _exec = _dispatch
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def run(op: str, args: Dict[str, Any]) -> DBResult:
    assert _exec, "database_module not initialized"
    out = await _exec(op, args)
    # normalize to DBResult
    if isinstance(out, DBResult):
        return out
    return DBResult(**out)  # expects {"rows":[...], "rowcount":N}
