"""MSSQL implementations for finance status code query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_json_many, run_json_one

__all__ = [
  "get_status_code_v1",
  "list_status_codes_v1",
]


async def list_status_codes_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_domain,
      element_code,
      element_name,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_status_codes
    WHERE (? IS NULL OR element_domain = ?)
    ORDER BY element_domain, element_code
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  element_domain = args.get("element_domain")
  return await run_json_many(sql, (element_domain, element_domain))


async def get_status_code_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_domain,
      element_code,
      element_name,
      element_description,
      element_status,
      element_created_on,
      element_modified_on
    FROM finance_status_codes
    WHERE element_domain = ?
      AND element_code = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["element_domain"], args["element_code"]))
