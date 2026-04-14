# ComponentBuilder & ContractQueryBuilder — Architecture Spec v0.2

## The Container Model

A component is either a **leaf** or a **container**. This distinction is
implicit in the existing data model — any component that has children in
`system_objects_component_tree` is a container. But we now need to make it
explicit because the ComponentBuilder needs to understand **slots**.

### What is a slot?

A container component has named positions where child components go. The
Workbench has two slots: NavigationSidebar (sequence 1) and ContentPanel
(sequence 2). The NavigationSidebar has three slots: SidebarHeader,
SidebarContent, SidebarFooter. These aren't arbitrary — the TSX code
renders `{children}` in specific layout positions.

The ComponentBuilder itself is a container with five slots:

```
ComponentBuilder (container, category: section)
├── ComponentPreview     (slot 1 — graphical canvas)
├── PropertyPanel        (slot 2 — property editor)
├── ComponentTreePanel   (slot 3 — tree composition)
├── QueryPreviewPanel    (slot 4 — derived query display)
└── ContractPanel        (slot 5 — I/O data contracts)
```

### Data model

The slot relationship is already expressed by `system_objects_component_tree`:
- `ref_parent_guid` = the container's tree node
- `ref_component_guid` = the child component
- `pub_sequence` = slot order

No schema changes needed. The container/slot relationship is emergent from
the tree structure. The ComponentBuilder just needs to understand this pattern
when editing: when you select a container component, you see its slots. When
you select a slot, the editor scope shifts to that sub-component.

### Editor scope

When editing ComponentBuilder itself:
- The **Preview** shows the five-panel layout schematically
- The **Tree** shows its five children
- The **Properties** show ComponentBuilder's own metadata
- Click a child slot → editor scope shifts to that component

When editing ComponentPreview (after clicking into it):
- The **Preview** shows ComponentPreview's own layout (the canvas)
- The **Tree** shows ComponentPreview's children (none — it's a leaf)
- The **Properties** show ComponentPreview's metadata
- Breadcrumb: ComponentBuilder → ComponentPreview
- Back button returns to ComponentBuilder scope

This recursive scoping is how every container works. It's the same pattern
the Workbench uses: you're always editing one component at a time, and
containers let you drill into their children.

---

## Self-Description: ComponentBuilder as Its Own First Entry

The ComponentBuilder is the first component to be fully defined in the
object tree as a composed component. Its five sub-components are registered
in `system_objects_components` and its composition tree is registered in
`system_objects_component_tree`.

### New component registrations (5)

| pub_name | pub_category | key_guid (deterministic) | pub_description |
|---|---|---|---|
| ComponentPreview | section | 3181D03C-15F6-554D-841C-623CD51635AA | Canvas-based abstract visual preview of the selected component's layout and composition. Pan/zoom/drag interaction. |
| PropertyPanel | section | CE8C2A85-BD51-5994-8278-005D0D4A4C1D | Property editor for the selected component. Shows name, category, description, default type, type controls, timestamps. |
| ComponentTreePanel | section | BE00786B-C289-5963-A8C8-3D0AFFC6D6A7 | Recursive tree editor for component composition. Add, delete, reorder child components. |
| QueryPreviewPanel | section | 4475FF51-0E31-5CE6-AFDA-DB3EC760200D | Read-only display of the derived SQL query from data bindings. Shows the query that ContractQueryBuilder would generate. |
| ContractPanel | section | 0FB4B481-AEB9-504D-AAEC-1B37650DC722 | Split panel showing inbound (request) and outbound (response) data contracts for the component. |

### ComponentBuilder composition tree (6 tree nodes)

| key_guid (deterministic) | path | ref_component_guid | sequence |
|---|---|---|---|
| 832BCD2B-DCB4-5472-91A5-289D50D64A19 | tree:ComponentBuilder | DA34C586 (ComponentBuilder) | 0 |
| 38FD4EA5-53BA-543F-A24B-2D2B2269D136 | tree:ComponentBuilder.ComponentPreview | 3181D03C (ComponentPreview) | 1 |
| 4B1E71A4-511B-574C-B4BE-C397A6412D84 | tree:ComponentBuilder.PropertyPanel | CE8C2A85 (PropertyPanel) | 2 |
| 3E218169-0A74-5C8A-8BC3-420B35E72FEB | tree:ComponentBuilder.ComponentTreePanel | BE00786B (ComponentTreePanel) | 3 |
| 04F0599A-DDBE-52BB-9D90-213FF01A7973 | tree:ComponentBuilder.QueryPreviewPanel | 4475FF51 (QueryPreviewPanel) | 4 |
| EA861C00-B174-592F-A060-0E05FA7649E7 | tree:ComponentBuilder.ContractPanel | 0FB4B481 (ContractPanel) | 5 |

The root node (832BCD2B) has no parent — it IS the ComponentBuilder.
The five children each reference their respective component registrations.

This means the ComponentBuilder can edit itself. When you navigate to
Components → ComponentBuilder in the object tree, the ComponentBuilder
loads, calls `getPageTree` for its own GUID, and shows its own five-slot
structure in the tree panel and preview canvas.

---

## ContractQueryBuilder Module

### Purpose

Reads a component's data bindings and mechanically derives:
1. The SQL query text that executes at render time
2. The output data model (Pydantic shape)
3. The input parameter model (if parameterized)

### File

`server/modules/contract_query_builder_module.py`

### Class

```python
class ContractQueryBuilderModule(BaseModule):
  """Derives queries and data models from component data bindings.

  Stateless analyzer. Given a page/component GUID, reads current
  binding state and produces derived artifacts. Called by
  ComponentBuilderModule on design events (binding added/removed/saved).
  """

  MODULE_GUID = "..." # uuid5(NS, 'module:contract_query_builder')

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.mark_ready()

  async def analyze_page(self, page_guid: str) -> dict:
    """Derive query and data contracts for a page from its bindings.

    Process:
      1. Load all data bindings for the page from
         system_objects_page_data_bindings
      2. Group by source_type:
         - literal: add to output model as STRING field
         - config: add to output model, resolve type from system_config
         - column: resolve column → table → type → FK constraints
         - function: resolve method → module, add to output model
      3. For column bindings: derive the query graph
         a. Collect distinct tables from column GUIDs
         b. Find FK join paths between tables via
            system_objects_database_constraints
         c. Build SELECT with aliases, JOINs, WHERE clause
      4. Build output model definition (field name, type, nullable, source)
      5. Build input model if query has parameters (e.g. @user_guid)

    Returns:
      {
        "page_slug": str,
        "query": str | None,
        "output_model": {
          "name": str,
          "fields": [
            {"name": str, "type": str, "nullable": bool, "source": str}
          ]
        },
        "input_model": dict | None,
        "tables": [str],
        "joins": [{"from": str, "to": str, "type": str}]
      }
    """

  async def derive_query(self, page_guid: str) -> str | None:
    """Derive just the SQL query text for a page.

    Returns None when the page has no column bindings.
    """

  async def save_derived_artifacts(
    self,
    page_guid: str,
    analysis: dict,
  ) -> None:
    """Commit the derived query and model to the database.

    Writes:
    1. UPSERT system_objects_rpc_models row for the output model
    2. UPSERT system_objects_rpc_model_fields for each field
    3. DELETE orphaned fields (aliases removed since last commit)
    4. Store query text in system_objects_pages.pub_derived_query
    5. Link model via system_objects_pages.ref_derived_model_guid

    All GUIDs are deterministic:
      Model: uuid5(NS, 'rpcmodel:PageData_{slug}_{version}')
      Field: uuid5(NS, 'rpcfield:PageData_{slug}_{version}.{alias}')
    """
```

### app.state registration

```python
# In server/lifespan.py startup:
app.state.contract_query_builder = ContractQueryBuilderModule(app)
await app.state.contract_query_builder.startup()
```

### RPC surface

Under `system.cms` subdomain (gated by ROLE_SERVICE_ADMIN):

```
urn:service:objects:analyze_page:1     → analyze_page
urn:service:objects:derive_query:1     → derive_query
```

### POC validation

On startup, `analyze_page` runs against the home page (GUID C75ECC15).
The home page has 8 literal bindings and zero column bindings, so:
- `query` = null (no database query needed)
- `output_model` = `PageData_home_1` with 8 STRING fields
- `input_model` = null
- `tables` = [] (empty)
- `joins` = [] (empty)

This validates the literal-binding-only path. The first real test is a
page with column bindings (UserProfile or similar) where the analyzer
must resolve column → table → FK → JOIN.

### Query derivation algorithm

For column bindings, the algorithm is:

1. **Collect columns:** Each `source_type = 'column'` binding has a
   `ref_column_guid`. Look up column name and `ref_table_guid` from
   `system_objects_database_columns`.

2. **Collect tables:** Distinct `ref_table_guid` values from step 1.
   Look up table name and schema from `system_objects_database_tables`.

3. **Find join paths:** If more than one table is involved, query
   `system_objects_database_constraints` to find FK relationships
   between the tables. This gives us the JOIN conditions.

4. **Build SELECT:** For each binding, add `{table_alias}.{column_name}
   AS {binding_alias}` to the SELECT list.

5. **Build FROM/JOIN:** Primary table in FROM, additional tables as
   JOINs based on the FK paths found in step 3.

6. **Build WHERE:** If any binding references a parameterized column
   (e.g., user_guid), add a WHERE clause with a named parameter.

7. **Assemble:** Combine into a complete SQL string.

The entire process is mechanical. No heuristics, no inference. The data
relationships in the object tree determine the query exactly.

---

## Data Model Changes Required

### system_objects_pages — two new columns

```sql
ALTER TABLE system_objects_pages
  ADD pub_derived_query NVARCHAR(MAX) NULL;

ALTER TABLE system_objects_pages
  ADD ref_derived_model_guid UNIQUEIDENTIFIER NULL;

ALTER TABLE system_objects_pages
  ADD CONSTRAINT FK_sop_derived_model
    FOREIGN KEY (ref_derived_model_guid)
    REFERENCES system_objects_rpc_models(key_guid);
```

These columns store the output of `save_derived_artifacts`:
- `pub_derived_query` — the actual SQL query text
- `ref_derived_model_guid` — FK to the derived output model

### system_objects_page_data_bindings — one new column

```sql
ALTER TABLE system_objects_page_data_bindings
  ADD ref_method_guid UNIQUEIDENTIFIER NULL;

ALTER TABLE system_objects_page_data_bindings
  ADD CONSTRAINT FK_sopdb_method
    FOREIGN KEY (ref_method_guid)
    REFERENCES system_objects_module_methods(key_guid);
```

Supports `pub_source_type = 'function'` bindings where the value is
computed by a server module method at runtime.

---

## Client-Side Panel Specifications

### ComponentPreview (canvas)

Canvas-based abstract renderer using the ServiceVisualizationPage patterns:
- HTML5 Canvas with `devicePixelRatio` support
- Pan (drag background), zoom (mousewheel), drag (nodes)
- Hover with glow/highlight effects

**What it draws for a container:**
- Outer rounded rectangle representing the container
- Inner rectangles for each slot, arranged vertically by sequence
- Slot labels showing component name + category
- Category-colored borders (blue=page, green=section, orange=control)
- Glow effects on hover matching the domain color palette

**What it draws for a leaf:**
- Single rounded rectangle with component name
- Type indicator if `ref_default_type_guid` is set
- Label display if `pub_label` is set
- fieldBinding display if set (monospace, green)

**Interaction:**
- Click slot → shifts editor scope to that sub-component
- Drag slot → reorder (updates sequence via RPC)
- Hover → glow highlight + name tooltip
- Pan/zoom like the schema visualizer

### PropertyPanel

Right-side vertical panel (280px width) showing editable properties:
- Component name (read-only — defined in TSX code)
- Category chip (read-only)
- Description (editable multiline TextField)
- Default Type (Select picker from all types)
- Type Controls (read-only list of mapped controls for this type)
- GUID (read-only monospace)
- Created/Modified timestamps (read-only)
- Save button

### ComponentTreePanel

The existing page-composer code extracted into a reusable sub-panel.
Shows the composition tree for the current component. For containers,
this shows the children. For leaves, shows "No composition tree."

### QueryPreviewPanel

Collapsible panel. Phase 1: placeholder with frame. Phase 2 (after
ContractQueryBuilder is implemented): shows the derived SQL with
syntax highlighting, output model fields, input parameters, table list,
and join paths.

The panel calls `analyze_page` via RPC and displays the result.

### ContractPanel

Collapsible split panel. Left: inbound data contract (request model
fields). Right: outbound data contract (response model fields).

Phase 1: Shows raw data binding rows from
`system_objects_page_data_bindings` — source type, alias, literal value
or column reference.

Phase 2: Shows the full typed model with field names, types, nullability,
and source indicators.

---

## Implementation Order

### Phase 1 — Structure + PropertyPanel (this Codex task)

1. Register 5 new components in `system_objects_components`
2. Create ComponentBuilder composition tree (6 tree nodes)
3. Create `builder/` directory with 5 sub-components + barrel
4. Rewrite `ComponentBuilder.tsx` as composed root
5. PropertyPanel fully functional (load detail, edit, save)
6. Other panels as visible placeholders with correct frames

### Phase 2 — ComponentPreview canvas

7. Canvas renderer with schematic drawing
8. Pan/zoom/drag interaction
9. Slot click → scope shift
10. Force layout for non-trivial trees

### Phase 3 — ContractQueryBuilder module

11. `contract_query_builder_module.py` — analyze_page, derive_query
12. RPC wiring
13. QueryPreviewPanel connected to live analysis
14. ContractPanel connected to live model data
15. Startup POC: analyze home page

### Phase 4 — Data binding editor

16. set_data_binding / remove_data_binding operations
17. Binding editor UI in the PropertyPanel or a new panel
18. Live re-analysis on binding changes
19. Save commits tree + bindings + derived artifacts atomically

---

## Deterministic GUIDs (Precomputed)

### Components
```
component:ComponentPreview      → 3181D03C-15F6-554D-841C-623CD51635AA
component:PropertyPanel         → CE8C2A85-BD51-5994-8278-005D0D4A4C1D
component:ComponentTreePanel    → BE00786B-C289-5963-A8C8-3D0AFFC6D6A7
component:QueryPreviewPanel     → 4475FF51-0E31-5CE6-AFDA-DB3EC760200D
component:ContractPanel         → 0FB4B481-AEB9-504D-AAEC-1B37650DC722
```

### Tree nodes (ComponentBuilder's own composition)
```
tree:ComponentBuilder                       → 832BCD2B-DCB4-5472-91A5-289D50D64A19
tree:ComponentBuilder.ComponentPreview      → 38FD4EA5-53BA-543F-A24B-2D2B2269D136
tree:ComponentBuilder.PropertyPanel         → 4B1E71A4-511B-574C-B4BE-C397A6412D84
tree:ComponentBuilder.ComponentTreePanel    → 3E218169-0A74-5C8A-8BC3-420B35E72FEB
tree:ComponentBuilder.QueryPreviewPanel     → 04F0599A-DDBE-52BB-9D90-213FF01A7973
tree:ComponentBuilder.ContractPanel         → EA861C00-B174-592F-A060-0E05FA7649E7
```
