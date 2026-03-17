from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CheckPurgedKeyParams,
  GetPurgeLogParams,
  ListPurgeLogsParams,
  UpsertPurgeLogParams,
)


def list_purge_logs_request(params: ListPurgeLogsParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_purge_log:list_purge_logs:1", payload=params.model_dump())


def get_purge_log_request(params: GetPurgeLogParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_purge_log:get_purge_log:1", payload=params.model_dump())


def check_purged_key_request(params: CheckPurgedKeyParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_purge_log:check_purged_key:1", payload=params.model_dump())


def upsert_purge_log_request(params: UpsertPurgeLogParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_purge_log:upsert_purge_log:1", payload=params.model_dump())
