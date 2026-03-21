"""Finance pipeline config subdomain handler implementations."""

from __future__ import annotations

from typing import Sequence

from queryregistry.dispatch import dispatch_subdomain_request
from queryregistry.models import DBRequest, DBResponse

from .services import (
  delete_pipeline_config_v1,
  get_pipeline_config_v1,
  list_pipeline_configs_v1,
  upsert_pipeline_config_v1,
)

__all__ = ["handle_pipeline_config_request"]

DISPATCHERS = {
  ("list", "1"): list_pipeline_configs_v1,
  ("get", "1"): get_pipeline_config_v1,
  ("upsert", "1"): upsert_pipeline_config_v1,
  ("delete", "1"): delete_pipeline_config_v1,
}


async def handle_pipeline_config_request(
  path: Sequence[str],
  request: DBRequest,
  *,
  provider: str,
) -> DBResponse:
  return await dispatch_subdomain_request(
    path,
    request,
    provider=provider,
    dispatchers=DISPATCHERS,
    detail="Unknown finance pipeline_config operation",
  )
