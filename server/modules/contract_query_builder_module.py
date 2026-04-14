from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from server.helpers.strings import deterministic_guid

from . import BaseModule


class ContractQueryBuilderModule(BaseModule):
  """Derives queries and data models from page data bindings.

  Stateless analyzer. Given a page GUID, reads current binding state
  and produces derived artifacts. Called by ComponentBuilder on design
  events and directly via RPC for preview.
  """

  MODULE_GUID = "5EB872F5-079A-55B2-A86C-72A435ACAF0E"

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()

    # POC: analyze the home page on startup to validate the pipeline
    try:
      home = await self._get_page_by_slug("home")
      if home:
        analysis = await self.analyze_page(str(home.get("key_guid", "")))
        await self.save_derived_artifacts(str(home.get("key_guid", "")), analysis)
        field_count = len(analysis.get("output_model", {}).get("fields", []))
        table_count = len(analysis.get("tables", []))
        model_name = analysis.get("output_model", {}).get("name", "none")
        logging.info(
          "[ContractQueryBuilder] home page: %d fields, %d tables, model=%s",
          field_count,
          table_count,
          model_name,
        )
    except Exception as exc:
      logging.warning("[ContractQueryBuilder] POC analysis failed: %s", exc)

    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def _get_page_by_slug(self, slug: str) -> dict[str, Any] | None:
    """Look up a page by slug."""
    from queryregistry.providers.mssql import run_json_one

    result = await run_json_one(
      """
      SELECT key_guid, pub_slug, pub_title
      FROM system_objects_pages
      WHERE pub_slug = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
      """,
      (slug,),
    )
    return dict(result.rows[0]) if result and result.rows else None

  async def analyze_page(self, page_guid: str) -> dict[str, Any]:
    """Derive query and data contracts for a page from its bindings."""
    from queryregistry.providers.mssql import run_json_many, run_json_one

    page = await run_json_one(
      """
      SELECT key_guid, pub_slug, pub_title
      FROM system_objects_pages
      WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
      """,
      (page_guid,),
    )
    page_row = dict(page.rows[0]) if page and page.rows else {}
    slug = str(page_row.get("pub_slug") or "unknown")

    bindings_result = await run_json_many(
      """
      SELECT
        b.key_guid,
        b.ref_component_node_guid AS component_node_guid,
        b.pub_source_type AS source_type,
        b.pub_literal_value AS literal_value,
        b.pub_config_key AS config_key,
        b.ref_column_guid AS column_guid,
        b.ref_method_guid AS method_guid,
        b.pub_alias AS alias
      FROM system_objects_page_data_bindings b
      WHERE b.ref_page_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
      FOR JSON PATH, INCLUDE_NULL_VALUES;
      """,
      (page_guid,),
    )
    bindings = [dict(row) for row in (bindings_result.rows if bindings_result else [])]

    literal_fields: list[dict[str, Any]] = []
    config_fields: list[dict[str, Any]] = []
    column_bindings: list[dict[str, Any]] = []
    function_fields: list[dict[str, Any]] = []

    for binding in bindings:
      source = str(binding.get("source_type") or "")
      alias = str(binding.get("alias") or "")
      if not alias:
        continue

      if source == "literal":
        literal_fields.append(
          {
            "name": alias,
            "type": "STRING",
            "nullable": False,
            "source": "literal",
          }
        )
      elif source == "config":
        config_fields.append(
          {
            "name": alias,
            "type": "STRING",
            "nullable": True,
            "source": "config",
          }
        )
      elif source == "column":
        column_guid = binding.get("column_guid")
        if column_guid:
          column_bindings.append(
            {
              "alias": alias,
              "column_guid": str(column_guid),
            }
          )
      elif source == "function":
        function_fields.append(
          {
            "name": alias,
            "type": "STRING",
            "nullable": True,
            "source": "function",
          }
        )

    column_fields: list[dict[str, Any]] = []
    tables_used: dict[str, dict[str, Any]] = {}
    query_text: str | None = None
    joins: list[dict[str, str]] = []

    if column_bindings:
      select_parts: list[str] = []
      alias_counter = 0

      for cb in column_bindings:
        col_result = await run_json_one(
          """
          SELECT
            c.pub_name AS column_name,
            c.pub_is_nullable AS is_nullable,
            c.ref_table_guid AS table_guid,
            t.pub_name AS table_name,
            t.pub_schema AS table_schema,
            ty.pub_name AS type_name
          FROM system_objects_database_columns c
          JOIN system_objects_database_tables t ON t.key_guid = c.ref_table_guid
          LEFT JOIN system_objects_types ty ON ty.key_guid = c.ref_type_guid
          WHERE c.key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
          FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
          """,
          (cb["column_guid"],),
        )
        col_row = dict(col_result.rows[0]) if col_result and col_result.rows else {}
        if not col_row:
          continue

        table_guid = str(col_row.get("table_guid") or "")
        table_name = str(col_row.get("table_name") or "")
        column_name = str(col_row.get("column_name") or "")
        type_name = str(col_row.get("type_name") or "STRING")
        is_nullable = bool(col_row.get("is_nullable"))

        if table_guid not in tables_used:
          alias_counter += 1
          table_alias = chr(ord("a") + alias_counter - 1) if alias_counter <= 26 else f"t{alias_counter}"
          tables_used[table_guid] = {
            "name": table_name,
            "schema": str(col_row.get("table_schema") or "dbo"),
            "alias": table_alias,
          }

        table_alias = tables_used[table_guid]["alias"]
        select_parts.append(f"{table_alias}.{column_name} AS {cb['alias']}")

        column_fields.append(
          {
            "name": cb["alias"],
            "type": type_name,
            "nullable": is_nullable,
            "source": "column",
          }
        )

      table_guids = list(tables_used.keys())
      if len(table_guids) > 1:
        joins = await self._find_join_paths(table_guids, tables_used)

      if select_parts:
        from_parts: list[str] = []
        first_table = True
        for _tg, tinfo in tables_used.items():
          if first_table:
            from_parts.append(f"FROM {tinfo['schema']}.{tinfo['name']} {tinfo['alias']}")
            first_table = False

        join_clauses: list[str] = []
        for join in joins:
          join_clauses.append(
            f"JOIN {join['to_table']} {join['to_alias']} "
            f"ON {join['to_alias']}.{join['to_column']} = "
            f"{join['from_alias']}.{join['from_column']}"
          )

        query_text = "SELECT\n  " + ",\n  ".join(select_parts)
        query_text += "\n" + "\n".join(from_parts)
        if join_clauses:
          query_text += "\n" + "\n".join(join_clauses)

    all_fields = literal_fields + config_fields + column_fields + function_fields
    model_name = f"PageData_{slug}_1"

    output_model = {
      "name": model_name,
      "fields": all_fields,
    }

    table_names = [t["name"] for t in tables_used.values()]
    join_descriptions = [
      {
        "from": f"{j.get('from_table', '')}.{j.get('from_column', '')}",
        "to": f"{j.get('to_table', '')}.{j.get('to_column', '')}",
        "type": "INNER JOIN",
      }
      for j in joins
    ]

    return {
      "page_slug": slug,
      "query": query_text,
      "output_model": output_model,
      "input_model": None,
      "tables": table_names,
      "joins": join_descriptions,
    }

  async def _find_join_paths(
    self,
    table_guids: list[str],
    tables_used: dict[str, dict[str, Any]],
  ) -> list[dict[str, str]]:
    """Find FK join paths between the involved tables."""
    from queryregistry.providers.mssql import run_json_many

    placeholders = ", ".join(f"TRY_CAST('{g}' AS UNIQUEIDENTIFIER)" for g in table_guids)
    result = await run_json_many(
      f"""
      SELECT
        c.ref_table_guid AS from_table_guid,
        col.pub_name AS from_column,
        c.ref_referenced_table_guid AS to_table_guid,
        ref_col.pub_name AS to_column
      FROM system_objects_database_constraints c
      JOIN system_objects_database_columns col
        ON col.key_guid = c.ref_column_guid
      JOIN system_objects_database_columns ref_col
        ON ref_col.key_guid = c.ref_referenced_column_guid
      WHERE c.ref_table_guid IN ({placeholders})
        AND c.ref_referenced_table_guid IN ({placeholders})
      FOR JSON PATH, INCLUDE_NULL_VALUES;
      """,
      (),
    )
    constraint_rows = [dict(row) for row in (result.rows if result else [])]

    joins: list[dict[str, str]] = []
    for cr in constraint_rows:
      from_tg = str(cr.get("from_table_guid") or "")
      to_tg = str(cr.get("to_table_guid") or "")
      if from_tg == to_tg:
        continue
      from_info = tables_used.get(from_tg)
      to_info = tables_used.get(to_tg)
      if not from_info or not to_info:
        continue
      joins.append(
        {
          "from_table": from_info["name"],
          "from_alias": from_info["alias"],
          "from_column": str(cr.get("from_column") or ""),
          "to_table": to_info["name"],
          "to_alias": to_info["alias"],
          "to_column": str(cr.get("to_column") or ""),
        }
      )

    return joins

  async def derive_query(self, page_guid: str) -> str | None:
    """Derive just the SQL query text for a page."""
    analysis = await self.analyze_page(page_guid)
    return analysis.get("query")

  async def save_derived_artifacts(
    self,
    page_guid: str,
    analysis: dict[str, Any],
  ) -> None:
    """Commit derived query and model to the database.

    Uses deterministic GUIDs for models and fields.
    """
    from queryregistry.providers.mssql import run_rows_many

    slug = str(analysis.get("page_slug") or "unknown")
    output_model = analysis.get("output_model") or {}
    model_name = str(output_model.get("name") or f"PageData_{slug}_1")
    fields = output_model.get("fields") or []
    query_text = analysis.get("query")

    model_guid = deterministic_guid("rpcmodel", model_name)

    await run_rows_many(
      """
      MERGE INTO system_objects_rpc_models AS target
      USING (SELECT
        TRY_CAST(? AS UNIQUEIDENTIFIER) AS key_guid,
        ? AS pub_name,
        ? AS pub_description,
        1 AS pub_version
      ) AS src
      ON target.key_guid = src.key_guid
      WHEN MATCHED THEN UPDATE SET
        pub_name = src.pub_name,
        pub_description = src.pub_description,
        priv_modified_on = SYSUTCDATETIME()
      WHEN NOT MATCHED THEN INSERT
        (key_guid, pub_name, pub_description, pub_version)
      VALUES
        (src.key_guid, src.pub_name, src.pub_description, src.pub_version);
      """,
      (model_guid, model_name, f"Derived output model for page '{slug}'"),
    )

    for ordinal, field in enumerate(fields, 1):
      field_name = str(field.get("name") or "")
      field_guid = deterministic_guid("rpcfield", f"{model_name}.{field_name}")

      type_name = str(field.get("type") or "STRING")
      type_guid_result = await run_rows_many(
        "SELECT key_guid FROM system_objects_types WHERE pub_name = ?;",
        (type_name,),
      )
      type_guid = None
      if type_guid_result and type_guid_result.rows:
        type_guid = str(dict(type_guid_result.rows[0]).get("key_guid") or "")

      await run_rows_many(
        """
        MERGE INTO system_objects_rpc_model_fields AS target
        USING (SELECT
          TRY_CAST(? AS UNIQUEIDENTIFIER) AS key_guid,
          TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_model_guid,
          ? AS pub_name,
          ? AS pub_ordinal,
          TRY_CAST(? AS UNIQUEIDENTIFIER) AS ref_type_guid,
          CAST(? AS BIT) AS pub_is_nullable
        ) AS src
        ON target.key_guid = src.key_guid
        WHEN MATCHED THEN UPDATE SET
          pub_name = src.pub_name,
          pub_ordinal = src.pub_ordinal,
          ref_type_guid = src.ref_type_guid,
          pub_is_nullable = src.pub_is_nullable,
          priv_modified_on = SYSUTCDATETIME()
        WHEN NOT MATCHED THEN INSERT
          (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, pub_is_nullable)
        VALUES
          (src.key_guid, src.ref_model_guid, src.pub_name, src.pub_ordinal,
           src.ref_type_guid, src.pub_is_nullable);
        """,
        (field_guid, model_guid, field_name, ordinal, type_guid, field.get("nullable", False)),
      )

    current_field_guids = [
      deterministic_guid("rpcfield", f"{model_name}.{f.get('name', '')}")
      for f in fields
    ]
    if current_field_guids:
      placeholders = ", ".join(f"'{g}'" for g in current_field_guids)
      await run_rows_many(
        f"""
        DELETE FROM system_objects_rpc_model_fields
        WHERE ref_model_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
          AND key_guid NOT IN ({placeholders});
        """,
        (model_guid,),
      )

    await run_rows_many(
      """
      UPDATE system_objects_pages
      SET pub_derived_query = ?,
          ref_derived_model_guid = TRY_CAST(? AS UNIQUEIDENTIFIER),
          priv_modified_on = SYSUTCDATETIME()
      WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
      """,
      (query_text, model_guid, page_guid),
    )
