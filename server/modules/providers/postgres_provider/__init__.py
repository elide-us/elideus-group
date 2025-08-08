from __future__ import annotations

from . import logic


class PostgreSQLProvider:
  """PostgreSQL database provider."""

  async def startup(self) -> None:
    """Initialize PostgreSQL connections if needed."""
    # Provider-specific startup logic goes here
    pass

  async def shutdown(self) -> None:
    """Cleanup PostgreSQL resources."""
    # Provider-specific shutdown logic goes here
    pass

  async def execute(self, query: str, *args, **kwargs):
    """Execute a write query against PostgreSQL.
    Provider-specific execution logic should be implemented in ``logic.execute``.
    """
    return await logic.execute(query, *args, **kwargs)

  async def fetch_one(self, query: str, *args, **kwargs):
    """Fetch a single record from PostgreSQL.
    Provider-specific fetch logic should be implemented in ``logic.fetch_one``.
    """
    return await logic.fetch_one(query, *args, **kwargs)

  async def fetch_many(self, query: str, *args, **kwargs):
    """Fetch multiple records from PostgreSQL.
    Provider-specific fetch logic should be implemented in ``logic.fetch_many``.
    """
    return await logic.fetch_many(query, *args, **kwargs)
