"""Reflection schema query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "ColumnRecord",
  "ForeignKeyRecord",
  "FullSchemaParams",
  "FullSchemaRecord",
  "IndexRecord",
  "SchemaRecord",
  "TableParams",
  "TableRecord",
  "ViewRecord",
]


class TableParams(BaseModel):
  """Payload targeting a table in reflection metadata."""

  model_config = ConfigDict(extra="forbid")

  table_schema: str
  name: str


class FullSchemaParams(BaseModel):
  """Empty payload for full schema introspection."""

  model_config = ConfigDict(extra="forbid")


class TableRecord(TypedDict):
  """Table metadata record from system_schema_tables."""

  recid: int
  element_schema: str
  element_name: str


class ColumnRecord(TypedDict):
  """Column metadata record resolved with EDT mappings."""

  tables_recid: int
  element_name: str
  element_nullable: bool
  element_default: str | None
  element_max_length: int | None
  element_is_primary_key: bool
  element_is_identity: bool
  element_ordinal: int
  element_mssql_type: str


class IndexRecord(TypedDict):
  """Index metadata record from system_schema_indexes."""

  tables_recid: int
  element_name: str
  element_columns: str
  element_is_unique: bool


class ForeignKeyRecord(TypedDict):
  """Foreign key metadata record from system_schema_foreign_keys."""

  tables_recid: int
  element_column_name: str
  referenced_tables_recid: int
  element_referenced_column: str


class ViewRecord(TypedDict):
  """View metadata record from system_schema_views."""

  element_schema: str
  element_name: str
  element_definition: str


class SchemaRecord(TypedDict):
  """Logical schema record matching composed table metadata."""

  tables: list[TableRecord]
  columns: list[ColumnRecord]
  indexes: list[IndexRecord]
  foreign_keys: list[ForeignKeyRecord]
  views: list[ViewRecord]


class FullSchemaRecord(TypedDict):
  """Composite schema response payload."""

  tables: list[TableRecord]
  columns: list[ColumnRecord]
  indexes: list[IndexRecord]
  foreign_keys: list[ForeignKeyRecord]
  views: list[ViewRecord]
