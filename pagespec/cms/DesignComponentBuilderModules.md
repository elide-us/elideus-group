# Module Design: ComponentBuilderModule + ContractQueryBuilderModule

## Overview

Two new server modules that are first-class participants in the object tree.
They get registered in `system_objects_modules` and `system_objects_module_methods`
alongside every other module. Their RPC functions get registered in the
`system_objects_rpc_*` tables. They eat their own dog food.

```
Object Tree
├── ...
├── Server Modules
│   ├── ...existing modules...
│   ├── ComponentBuilderModule          ★ NEW
│   │   ├── create_tree_node
│   │   ├── update_tree_node
│   │   ├── delete_tree_node
│   │   ├── move_tree_node
│   │   ├── set_data_binding
│   │   ├── remove_data_binding
│   │   └── save_page_definition
│   └── ContractQueryBuilderModule      ★ NEW
│       ├── analyze_page
│       └── derive_query
├── ...
```

---

## Module 1: ComponentBuilderModule

**File:** `server/modules/component_builder_module.py`
**Class:** `ComponentBuilderModule`
**app.state:** `component_builder`
**Module path:** `server.modules.component_builder_module`

### Responsibility

Manages the component tree for page definitions. CRUD operations on tree nodes,
data binding management, and save coordination. On save, it commits the tree
state and calls ContractQueryBuilderModule to derive the final query/model.

### Methods

```python
class ComponentBuilderModule(BaseModule):
    """Manages component tree composition for page definitions."""

    async def startup(self):
        self.db = self.app.state.db
        await self.db.on_ready()
        self.contract_builder = self.app.state.contract_query_builder
        self.mark_ready()

    # --- Tree node CRUD ---

    async def create_tree_node(
        self,
        ref_page_guid: str,
        ref_parent_guid: str | None,
        component_name: str,
        pub_label: str | None = None,
        pub_field_binding: str | None = None,
        pub_sequence: int = 0,
    ) -> dict:
        """Insert a new node into a page's component tree.

        1. Look up component GUID from system_objects_components by name
        2. Generate deterministic tree node GUID from tree path
        3. INSERT into system_objects_component_tree
        4. Return the new node
        """

    async def update_tree_node(
        self,
        key_guid: str,
        pub_label: str | None = None,
        pub_field_binding: str | None = None,
        pub_sequence: int | None = None,
    ) -> dict:
        """Update properties on an existing tree node.

        Supports partial updates — only non-None values are applied.
        This is a per-field dispatch: one property change, one UPDATE.
        """

    async def delete_tree_node(self, key_guid: str) -> dict:
        """Delete a tree node and cascade to all descendants.

        1. Recursive CTE to find all descendant nodes
        2. Delete data bindings for all affected nodes
        3. Delete the nodes themselves (leaves first, bottom-up)
        4. Return count of deleted nodes
        """

    async def move_tree_node(
        self,
        key_guid: str,
        ref_new_parent_guid: str | None,
        pub_new_sequence: int,
    ) -> dict:
        """Move a node to a new parent and/or sequence position."""

    # --- Data binding management ---

    async def set_data_binding(
        self,
        ref_page_guid: str,
        ref_component_node_guid: str,
        pub_source_type: str,          # 'column' | 'literal' | 'config' | 'function'
        ref_column_guid: str | None = None,
        pub_literal_value: str | None = None,
        pub_config_key: str | None = None,
        ref_method_guid: str | None = None,
        pub_alias: str | None = None,
    ) -> dict:
        """Set or update a data binding for a component tree node.

        UPSERT pattern: if binding exists for this page+node, update it.
        If not, insert a new one with deterministic GUID.

        After setting the binding, dispatch analysis event to
        ContractQueryBuilderModule.
        """

    async def remove_data_binding(
        self,
        ref_page_guid: str,
        ref_component_node_guid: str,
    ) -> dict:
        """Remove a data binding. Dispatch analysis event after."""

    # --- Save ---

    async def save_page_definition(self, ref_page_guid: str) -> dict:
        """Commit the page definition.

        1. Call ContractQueryBuilderModule.analyze_page(ref_page_guid)
        2. The analyzer derives query + model and writes them
        3. Return the finalized page state
        """

    # --- Component palette ---

    async def list_available_components(self) -> list[dict]:
        """Return all registered components from system_objects_components.

        This feeds the component toolbox/tray in the UI.
        """

    async def get_page_tree(self, ref_page_guid: str) -> dict:
        """Return the full component tree for a page.

        Same CTE walk as CmsWorkbenchModule but scoped to a page's tree
        (using ref_page_guid or the page's ref_root_component_guid).
        """
```

### Events → ContractQueryBuilderModule

The ComponentBuilder dispatches to the ContractQueryBuilder on these events:
- `set_data_binding` — a new column/config/function reference was added
- `remove_data_binding` — a data reference was removed
- `save_page_definition` — final save, commit the derived artifacts

The dispatch is a direct async call: `await self.contract_builder.analyze_page(page_guid)`.
No message queue, no event bus. Direct module-to-module call. The ContractQueryBuilder
returns the analysis result, and the ComponentBuilder can surface it to the client
(e.g., "your page needs 2 tables, 5 columns, 1 join").

---

## Module 2: ContractQueryBuilderModule

**File:** `server/modules/contract_query_builder_module.py`
**Class:** `ContractQueryBuilderModule`
**app.state:** `contract_query_builder`
**Module path:** `server.modules.contract_query_builder_module`

### Responsibility

Analyzes a page's data bindings and derives the query and data model.
Stateless — given a page GUID, it reads the current binding state and produces
the derived artifacts. Called by ComponentBuilderModule on design events.

### Methods

```python
class ContractQueryBuilderModule(BaseModule):
    """Derives queries and data models from page data bindings."""

    async def startup(self):
        self.db = self.app.state.db
        await self.db.on_ready()
        self.mark_ready()

    async def analyze_page(self, page_guid: str) -> dict:
        """Derive query and data contracts for a page from its bindings.

        Called on design events (binding added/removed/changed).
        Deterministic — same bindings always produce the same output.
        On re-analysis, returns updated results; commit writes them
        to the database using deterministic GUIDs (update in place).

        Process:
          1. Load page definition (slug for naming, guid for binding lookup)
          2. Load all data bindings for the page
          3. For column bindings: resolve column → table → type → FK constraints
          4. Derive the query graph from the involved tables and join paths
          5. Build the SQL query text
          6. Build the input/output model definitions

        Returns client-friendly values (names, not GUIDs):

        {
          "page_slug": "home",

          "query": null,
            -- The actual SQL query string that will be stored in the database.
            -- null when no column bindings exist (all literal/config/function).
            -- For a page with column bindings, this is the real query:
            -- "SELECT u.pub_display AS display_name, u.pub_email AS email,
            --  c.element_value AS credits FROM account_users u
            --  JOIN users_credits c ON c.ref_user_guid = u.key_guid
            --  WHERE u.key_guid = @user_guid"

          "output_model": {
            "name": "PageData_home_1",
            "fields": [
              {"name": "banner_image", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "link_discord", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "link_github", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "link_tiktok", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "link_bluesky", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "link_suno", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "link_patreon", "type": "STRING", "nullable": false, "source": "literal"},
              {"name": "copyright", "type": "STRING", "nullable": false, "source": "literal"}
            ]
          },

          "input_model": null,
            -- null when the page has no parameterized query.
            -- For a page like UserProfile that needs a user_guid parameter:
            -- {"name": "PageParams_user_profile_1",
            --  "fields": [{"name": "user_guid", "type": "UUID", "nullable": false}]}

          "tables": [],
            -- List of table names involved in the query.
            -- Empty for all-literal pages.
            -- e.g., ["account_users", "users_credits"]

          "joins": []
            -- Join path descriptions, human readable.
            -- e.g., [{"from": "users_credits.ref_user_guid",
            --         "to": "account_users.key_guid",
            --         "type": "INNER JOIN"}]
        }
        """

    async def derive_query(self, page_guid: str) -> str | None:
        """Derive just the SQL query text for a page.

        Returns the query as a string for display and storage.
        Returns None when the page has no column bindings.
        This is the actual query that gets stored in the database
        and executed at page load time.
        """

    async def save_derived_artifacts(self, page_guid: str, analysis: dict) -> None:
        """Commit the derived query and model to the database.

        Called by ComponentBuilderModule.save_page_definition on commit.
        All GUIDs are deterministic from page slug + field aliases.
        On re-commit, existing rows are UPDATED in place.

        GUID formulas:
          Model: uuid5(NS, 'rpcmodel:PageData_{slug}_{version}')
          Field: uuid5(NS, 'rpcfield:PageData_{slug}_{version}.{field_alias}')

        Writes:
        1. UPSERT system_objects_rpc_models row for the output model
           (and input model if the page has query parameters)
        2. UPSERT system_objects_rpc_model_fields for each field
        3. DELETE orphaned fields (aliases removed since last commit)
        4. Store the query text: UPDATE system_objects_pages
           SET pub_derived_query = analysis["query"]
        5. Link the model: UPDATE system_objects_pages
           SET ref_derived_model_guid = deterministic model GUID
        """
```

### Query Derivation — The Algorithm

For a page with these column bindings:
```
binding: display_name → account_users.pub_display (STRING)
binding: email        → account_users.pub_email (STRING)
binding: credits      → users_credits.element_value (INT32)
```

Step 1: Resolve columns to tables:
```
account_users:   pub_display, pub_email
users_credits:   element_value
```

Step 2: Find FK path between tables:
```
system_objects_database_constraints tells us:
  users_credits.ref_user_guid → account_users.key_guid
```

Step 3: Derive query:
```sql
SELECT
  u.pub_display AS display_name,
  u.pub_email AS email,
  c.element_value AS credits
FROM account_users u
JOIN users_credits c ON c.ref_user_guid = u.key_guid
WHERE u.key_guid = @user_guid
```

Step 4: Derive model:
```
PageData_user_profile_1:
  display_name: STRING (not null)
  email: STRING (not null)
  credits: INT32 (nullable)
```

Everything is mechanical. The tables, columns, types, and FK paths are all
in the object tree. The query writes itself.

### For the Home Page (POC)

The home page has zero column bindings — all literal and config. So:

```
analyze_page("home"):
  bindings:
    banner_image  → literal: "/static/assets/elideus_group_green.png"
    link_discord  → literal: "https://discord.gg/xXUZFTuzSw"
    link_github   → literal: "https://github.com/elide-us"
    link_tiktok   → literal: "https://www.tiktok.com/@elide.us"
    link_bluesky  → literal: "https://bsky.app/profile/elideusgroup.com"
    link_suno     → literal: "https://suno.com/@elideus"
    link_patreon  → literal: "https://patreon.com/Elideus"
    copyright     → literal: "© 2026 The Elideus Group"

  tables: [] (none — all literals)
  columns: [] (none)
  joins: [] (none)
  query: null (no database query needed)
  model:
    name: PageData_home_1
    fields:
      banner_image: STRING
      link_discord: STRING
      link_github: STRING
      link_tiktok: STRING
      link_bluesky: STRING
      link_suno: STRING
      link_patreon: STRING
      copyright: STRING
```

Trivial, but proves the pipeline. The real test is SystemConfigPage where
bindings point to `system_config.element_key` and `system_config.element_value`.

---

## Object Tree Registration

Both modules get registered in the system_objects_* tables on deployment:

### system_objects_modules (2 new rows)

```
uuid5(NS, 'module:component_builder')      → ComponentBuilderModule
uuid5(NS, 'module:contract_query_builder')  → ContractQueryBuilderModule
```

### system_objects_module_methods (~10 new rows)

```
component_builder.create_tree_node
component_builder.update_tree_node
component_builder.delete_tree_node
component_builder.move_tree_node
component_builder.set_data_binding
component_builder.remove_data_binding
component_builder.save_page_definition
component_builder.list_available_components
component_builder.get_page_tree
contract_query_builder.analyze_page
contract_query_builder.derive_query
```

### system_objects_rpc_functions (under system.cms subdomain)

```
urn:system:cms:create_tree_node:1     → component_builder.create_tree_node
urn:system:cms:update_tree_node:1     → component_builder.update_tree_node
urn:system:cms:delete_tree_node:1     → component_builder.delete_tree_node
urn:system:cms:move_tree_node:1       → component_builder.move_tree_node
urn:system:cms:set_data_binding:1     → component_builder.set_data_binding
urn:system:cms:remove_data_binding:1  → component_builder.remove_data_binding
urn:system:cms:save_page_definition:1 → component_builder.save_page_definition
urn:system:cms:list_components:1      → component_builder.list_available_components
urn:system:cms:get_page_tree:1        → component_builder.get_page_tree
urn:system:cms:analyze_page:1         → contract_query_builder.analyze_page
```

All gated by ROLE_SERVICE_ADMIN (domain-level) since page building is an admin activity.

---

## POC: Startup Processing of Home Page

For the initial proof of concept, ContractQueryBuilderModule runs `analyze_page`
for the home page on startup. This validates the entire pipeline:

```python
async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()

    # POC: analyze the home page on startup
    home_page = await self._get_page_by_slug("home")
    if home_page:
        analysis = await self.analyze_page(home_page["key_guid"])
        await self.save_derived_artifacts(home_page["key_guid"], analysis)
        logging.info(
            "[ContractQueryBuilder] home page: %d bindings, %d tables, model=%s",
            len(analysis.get("columns", [])) + len(analysis.get("literals", [])),
            len(analysis.get("tables", [])),
            analysis.get("model", {}).get("name", "none"),
        )

    self.mark_ready()
```

After this runs, `system_objects_rpc_models` will have a `PageData_home_1` row,
and `system_objects_rpc_model_fields` will have 8 field rows (one per binding).
The model is the first mechanically-derived data contract in the system.

---

## Interaction Flow

```
Designer clicks "Add LinkButton" in ComponentBuilder UI
  → ComponentBuilderModule.create_tree_node(page, parent, "LinkButton", ...)
  → New tree node inserted
  → Returns: { component: "LinkButton", label: null, sequence: 8 }

Designer sets label to "Twitter"
  → ComponentBuilderModule.update_tree_node(node, label="Twitter")
  → Returns: { component: "LinkButton", label: "Twitter", sequence: 8 }

Designer opens data binding panel, sets source=literal, value="https://x.com/..."
  → ComponentBuilderModule.set_data_binding(page, node, "literal", literal_value="https://x.com/...", alias="link_twitter")
  → Binding saved
  → ComponentBuilderModule dispatches → ContractQueryBuilderModule.analyze_page(page)
  → Returns to client:
    {
      "page_slug": "home",
      "query": null,
      "output_model": {
        "name": "PageData_home_1",
        "fields": [
          {"name": "banner_image", "type": "STRING", "nullable": false, "source": "literal"},
          ... 8 existing fields ...
          {"name": "link_twitter", "type": "STRING", "nullable": false, "source": "literal"}
        ]
      },
      "input_model": null,
      "tables": [],
      "joins": []
    }
  → Client displays: query panel shows "No database query (all static values)"
  → Client displays: model panel shows PageData_home_1 with 9 STRING fields

Designer clicks "Save"
  → ComponentBuilderModule.save_page_definition(page)
  → Calls ContractQueryBuilderModule.analyze_page(page) — final pass
  → Calls ContractQueryBuilderModule.save_derived_artifacts(page, analysis)
  → Derived model written/updated in system_objects_rpc_models + model_fields
  → Derived query stored in system_objects_pages.pub_derived_query (null for home)
  → Model linked via system_objects_pages.ref_derived_model_guid
  → Returns: { saved: true, model_name: "PageData_home_1", field_count: 9 }
```

---

## Data Model Changes

### New column on system_objects_page_data_bindings

```sql
ALTER TABLE system_objects_page_data_bindings
  ADD ref_method_guid UNIQUEIDENTIFIER NULL;

ALTER TABLE system_objects_page_data_bindings
  ADD CONSTRAINT FK_sopdb_method FOREIGN KEY (ref_method_guid)
    REFERENCES system_objects_module_methods(key_guid);
```

This supports `pub_source_type = 'function'` bindings where the value
is computed by a server module method at runtime.

### New column on system_objects_pages

```sql
ALTER TABLE system_objects_pages
  ADD ref_derived_model_guid UNIQUEIDENTIFIER NULL,
      pub_derived_query      NVARCHAR(MAX)    NULL;

ALTER TABLE system_objects_pages
  ADD CONSTRAINT FK_sop_derived_model FOREIGN KEY (ref_derived_model_guid)
    REFERENCES system_objects_rpc_models(key_guid);
```

`ref_derived_model_guid` links the page to its mechanically-derived output model.
`pub_derived_query` stores the derived SQL query text — the actual query that
gets executed at page load time for column-sourced data. NULL when the page
has no column bindings (all literal/config/function).

---

## What This Proves

Once both modules run and the home page is processed on startup:

1. The ContractQueryBuilderModule can read a page's bindings and produce a model
2. The model is written to system_objects_rpc_models + model_fields
3. The model is linked back to the page via ref_derived_model_guid
4. The entire chain from component tree → data binding → model derivation → storage is mechanical
5. No hand-written queries, no hand-written models — everything derived from the binding definitions

The ComponentBuilderModule methods become the API surface for the dev mode UI.
The ContractQueryBuilderModule is the invisible engine that makes the data contracts
self-assembling.

Content Forge, meet your brain.