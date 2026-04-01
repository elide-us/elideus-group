"""Pydantic models for service.reflection RPC operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DescribeTableRequest1(BaseModel):
  table_name: str
  table_schema: str = "dbo"


class DumpTableRequest1(BaseModel):
  table_name: str
  table_schema: str = "dbo"
  max_rows: int = Field(default=100, ge=0, le=1000)


class QueryInfoSchemaRequest1(BaseModel):
  view_name: str
  filter_column: str | None = None
  filter_value: str | None = None


class SchemaVersionResponse1(BaseModel):
  version: Any


class TableListResponse1(BaseModel):
  tables: list[dict[str, Any]]


class DescribeTableResponse1(BaseModel):
  columns: list[dict[str, Any]]
  indexes: list[dict[str, Any]]
  foreign_keys: list[dict[str, Any]]


class DumpTableResponse1(BaseModel):
  rows: list[dict[str, Any]]
  truncated: bool
  total_rows: int


class DomainsResponse1(BaseModel):
  domains: list[dict[str, Any]]


class RpcEndpointsResponse1(BaseModel):
  endpoints: list[str]
