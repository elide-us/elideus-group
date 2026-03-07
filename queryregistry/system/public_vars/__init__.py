"""System public_vars query handler package."""

from queryregistry.models import DBRequest


def get_version_request() -> DBRequest:
  return DBRequest(op="db:system:public_vars:get_version:1", payload={})


def get_hostname_request() -> DBRequest:
  return DBRequest(op="db:system:public_vars:get_hostname:1", payload={})


def get_repo_request() -> DBRequest:
  return DBRequest(op="db:system:public_vars:get_repo:1", payload={})


__all__ = [
  "get_hostname_request",
  "get_repo_request",
  "get_version_request",
]
