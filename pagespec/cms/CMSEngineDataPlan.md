# CMS Engine Data Plan — v0.12.3.0

**Purpose:** Define the new tables, seed data, and object tree registrations required to support the CMS engine and the Workbench template. This is the data foundation that Codex will build from.

**Convention reminder:**
- Column prefixes: `key_*` (PK), `pub_*` (functional), `priv_*` (audit), `ref_*` (FK), `ext_*` (future)
- PK strategy: deterministic UUID5 for canonical definitions, random GUID for instance data
- UUID5 namespace: `DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67`
- Key formulas listed per table

---

## 0. Prerequisites: Missing Type

Add back the DECIMAL_28_12 type that was dropped from the v0.12.1.0 seed.

```
uuid5(NS, 'type:DECIMAL_28_12') → needs generation

INSERT INTO system_objects_types:
  pub_name:            DECIMAL_28_12
  pub_mssql_type:      decimal(28,12)
  pub_postgresql_type: numeric(28,12)
  pub_mysql_type:      decimal(28,12)
  pub_python_type:     float
  pub_typescript_type: number
  pub_json_type:       number
  pub_odbc_type_code:  3
  pub_max_length:      NULL
  pub_notes:           High-precision staging decimal (28,12). Used in staging tables for full provider precision before GL quantization.
```

After this insert: **12 types** in the registry.

---

## 1. New Tables

### 1.1 `system_objects_components` — Component Registry

Registered component types — the finite, code-defined catalog of React components. Each entry maps a component name to a category and optionally to a default type.

```
Key formula: uuid5(NS, 'component:{pub_name}')

Columns:
  key_guid              UNIQUEIDENTIFIER  NOT NULL  PK
  pub_name              NVARCHAR(128)     NOT NULL  UNIQUE  -- React component name (e.g., "SortableGrid")
  pub_category          NVARCHAR(32)      NOT NULL          -- "page" | "section" | "grid" | "control"
  pub_description       NVARCHAR(512)     NULL
  ref_default_type_guid UNIQUEIDENTIFIER  NULL      FK → system_objects_types.key_guid
  priv_created_on       DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
  priv_modified_on      DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
```

### 1.2 `system_objects_component_tree` — Page Composition Tree

The recursive component tree. Each node is a component instance: which registered component it uses, where it sits in the hierarchy, what data it binds to.

```
Key formula: uuid5(NS, 'tree:{full_path_from_root}')

  The natural key is the full dot-delimited path from the root node to this node.
  Each segment is the component name, with a colon suffix for disambiguation
  when the same component type appears multiple times under the same parent:

    uuid5(NS, 'tree:Workbench')
    uuid5(NS, 'tree:Workbench.NavigationSidebar')
    uuid5(NS, 'tree:Workbench.NavigationSidebar.SidebarHeader')
    uuid5(NS, 'tree:Workbench.NavigationSidebar.SidebarHeader.HamburgerToggle')
    uuid5(NS, 'tree:Workbench.NavigationSidebar.SidebarContent.NavigationTreeView')

  When disambiguation is needed (same component type, different bindings):
    uuid5(NS, 'tree:UserDetail.FormSection_identity.StringControl:display_name')
    uuid5(NS, 'tree:UserDetail.FormSection_identity.StringControl:email')

  This follows the column pattern: uuid5(NS, 'column:{table}.{column}')
  Same tree structure = same GUID in every database instance.

Columns:
  key_guid                UNIQUEIDENTIFIER  NOT NULL  PK
  ref_parent_guid         UNIQUEIDENTIFIER  NULL      FK → self (NULL = root node)
  ref_component_guid      UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_components.key_guid
  ref_type_guid           UNIQUEIDENTIFIER  NULL      FK → system_objects_types.key_guid (override)
  pub_label               NVARCHAR(256)     NULL          -- display label
  pub_field_binding       NVARCHAR(128)     NULL          -- field name in RPC response
  pub_sequence            INT               NOT NULL  DEFAULT 0
  pub_rpc_operation       NVARCHAR(256)     NULL          -- RPC function name for data loading
  pub_rpc_contract        NVARCHAR(256)     NULL          -- TypeScript type name of response
  pub_mutation_operation  NVARCHAR(256)     NULL          -- RPC function name for writes
  pub_is_default_editable BIT               NOT NULL  DEFAULT 0  -- default editability hint
  priv_created_on         DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
  priv_modified_on        DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()

Indexes:
  IX_soct_parent    ON (ref_parent_guid)        -- tree traversal
  IX_soct_component ON (ref_component_guid)     -- component lookup
  UQ_soct_parent_sequence ON (ref_parent_guid, pub_sequence)  -- order within parent
```

### 1.3 `system_objects_routes` — Route-to-Page Bindings

Maps a URL route path to a root component tree node. Replaces `frontend_pages`.

```
Key formula: uuid5(NS, 'route:{pub_path}')

Columns:
  key_guid              UNIQUEIDENTIFIER  NOT NULL  PK
  pub_path              NVARCHAR(512)     NOT NULL  UNIQUE  -- route path (e.g., "/user-manager")
  pub_title             NVARCHAR(256)     NULL              -- page title for browser tab
  ref_root_node_guid    UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_component_tree.key_guid
  pub_sequence          INT               NOT NULL  DEFAULT 0  -- nav ordering
  pub_icon              NVARCHAR(64)      NULL              -- Material icon name for nav
  ref_parent_route_guid UNIQUEIDENTIFIER  NULL      FK → self (NULL = top-level route)
  ref_required_role_guid UNIQUEIDENTIFIER NULL      FK → system_auth_roles.key_guid
  pub_is_active         BIT               NOT NULL  DEFAULT 1
  priv_created_on       DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
  priv_modified_on      DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()

Indexes:
  IX_sor_parent     ON (ref_parent_route_guid)  -- tree nav
  IX_sor_root_node  ON (ref_root_node_guid)     -- page lookup
```

### 1.4 `system_objects_type_controls` — Type-to-Control Mapping

Maps types to their rendering controls. Many-to-many with a default flag.

```
Key formula: uuid5(NS, 'typecontrol:{type_name}.{component_name}')

  Deterministic — same type + control combination = same GUID everywhere.
  Example: uuid5(NS, 'typecontrol:STRING.StringControl')
           uuid5(NS, 'typecontrol:STRING.DropdownSelect')

Columns:
  key_guid              UNIQUEIDENTIFIER  NOT NULL  PK
  ref_type_guid         UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_types.key_guid
  ref_component_guid    UNIQUEIDENTIFIER  NOT NULL  FK → system_objects_components.key_guid
  pub_is_default        BIT               NOT NULL  DEFAULT 0
  priv_created_on       DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()
  priv_modified_on      DATETIMEOFFSET(7) NOT NULL  DEFAULT SYSUTCDATETIME()

Indexes:
  UQ_sotc_type_component ON (ref_type_guid, ref_component_guid)  -- no duplicate mappings
```

---

## 2. Seed Data: Component Registry

All deterministic UUID5 from `uuid5(NS, 'component:{name}')`.

Only components required for the Workbench and its immediate dependencies are registered in this pass. Additional components (grids, page templates, leaf controls for page specs) will be registered as they are built.

### Architecture Note: Two Modes, One Shell

The Workbench is always the root. It always renders a sidebar and a content panel. Mode determines what fills them:

```
Workbench (always present)
├── NavigationSidebar
│   ├── SidebarHeader → HamburgerToggle
│   ├── SidebarContent
│   │   ├── [Standard Mode] NavigationTreeView (routes)
│   │   └── [Dev Mode]      ObjectTreeView (object tree)
│   └── SidebarFooter → LoginControl, UserProfileControl, DevModeToggle
└── ContentPanel
    ├── [Standard Mode] CMS-rendered page (resolved by current route)
    └── [Dev Mode]      ObjectEditor (for selected object tree node)
```

ObjectEditor is **content** rendered inside the ContentPanel when in dev mode — it is not a sibling of the Workbench. The ContentPanel is a generic host; its child is determined by mode + context.

### Page Components

| pub_name | pub_category | pub_description |
|---|---|---|
| `Workbench` | page | Root application shell. Contains NavigationSidebar and ContentPanel. Manages mode state (standard/dev). |

### Section Components

| pub_name | pub_category | pub_description |
|---|---|---|
| `NavigationSidebar` | section | Vertical sidebar with header, content, and footer slots. |
| `SidebarHeader` | section | Top-pinned container within the sidebar. |
| `SidebarContent` | section | Scrollable middle container. Renders NavigationTreeView or ObjectTreeView based on mode. |
| `SidebarFooter` | section | Bottom-pinned container within the sidebar. |
| `NavigationTreeView` | section | Hierarchical tree of navigable routes. Role-masked. Standard mode. |
| `ObjectTreeView` | section | Live editable view of system_objects_* tree. Dev mode. |
| `ContentPanel` | section | Main content area. Hosts CMS-rendered pages (standard mode) or ObjectEditor (dev mode). |
| `ObjectEditor` | section | Object detail editor rendered inside ContentPanel in dev mode. Loads fields for selected tree node. |
| `CollapsibleSection` | section | Expandable/collapsible container with header label. Used by ObjectEditor for grouped fields. |

### Control Components

| pub_name | pub_category | ref_default_type | pub_description |
|---|---|---|---|
| `NavigationItem` | control | *(null)* | Clickable route item in navigation tree. Icon + label. |
| `ObjectTreeNode` | control | *(null)* | Node in the object tree. Icon + name, expand/collapse. |
| `LoginControl` | control | *(null)* | Authentication widget. Login/user state. |
| `UserProfileControl` | control | *(null)* | User avatar, name, logout action. |
| `DevModeToggle` | control | BOOL | Toggle for switching sidebar between standard and dev mode. ROLE_SERVICE_ADMIN only. |
| `HamburgerToggle` | control | *(null)* | Sidebar drawer expand/collapse button. |
| `StringControl` | control | STRING | Single-line text input/display. |
| `BoolToggle` | control | BOOL | Toggle switch / checkbox. |
| `IntControl` | control | INT32 | Integer input with optional formatting. |
| `ReadOnlyDisplay` | control | *(null)* | Generic read-only value display for any type. Fallback for non-editable fields. |
| `ButtonLinkControl` | control | *(null)* | Clickable button-style link to a route or URL. Used for homepage navigation and action links. |

**Total: 1 page + 9 section + 11 control = 21 component registrations.**

*Future registrations (added as pages are built): SummaryAndGridPage, HeaderDetailPage, StaticContentPage, TabbedPage, FeedPage, FormSection, SortableGrid, EditableGrid, DecimalControl, DatePicker, DropdownSelect, MultiSelect, ButtonAction, TextAreaControl, MarkdownEditor, LinkControl, ChipList, ImageUpload, SliderControl, etc.*

---

## 3. Seed Data: Type-to-Control Mappings

Default mappings only for types used by the initial control set. Additional mappings are added as controls are registered.

| Type | Default Control | Notes |
|---|---|---|
| INT32 | IntControl | ObjectEditor integer fields |
| STRING | StringControl | ObjectEditor string fields |
| BOOL | BoolToggle | ObjectEditor boolean fields, DevModeToggle |

All other types (INT64, UUID, DATETIME_TZ, TEXT, DATE, DECIMAL_19_5, DECIMAL_28_12, INT8, INT64_IDENTITY) default to `ReadOnlyDisplay` until their dedicated controls are registered.

| Type | Default Control | Notes |
|---|---|---|
| INT64 | ReadOnlyDisplay | |
| INT64_IDENTITY | ReadOnlyDisplay | Auto-generated, never editable |
| UUID | ReadOnlyDisplay | |
| DATETIME_TZ | ReadOnlyDisplay | |
| TEXT | ReadOnlyDisplay | |
| INT8 | ReadOnlyDisplay | |
| DATE | ReadOnlyDisplay | |
| DECIMAL_19_5 | ReadOnlyDisplay | |
| DECIMAL_28_12 | ReadOnlyDisplay | |

**Total: 12 default mappings (3 to specific controls, 9 to ReadOnlyDisplay).**

*As controls like DecimalControl, DatePicker, TextAreaControl are registered in future passes, the default mappings for their types will be updated to point to the new controls.*

---

## 4. Seed Data: Workbench Component Tree

The Workbench page's component tree — the first page definition expressed through the CMS engine. All tree node GUIDs are deterministic UUID5 from their full path.

The tree defines everything that *could* render. Mode state (standard vs dev) determines which children of SidebarContent and ContentPanel are active at any given time.

```
Key path                                                              Component            Mode
─────────────────────────────────────────────────────────────────────  ───────────────────  ─────────
tree:Workbench                                                        Workbench            always
tree:Workbench.NavigationSidebar                                      NavigationSidebar    always
tree:Workbench.NavigationSidebar.SidebarHeader                        SidebarHeader        always
tree:Workbench.NavigationSidebar.SidebarHeader.HamburgerToggle        HamburgerToggle      always
tree:Workbench.NavigationSidebar.SidebarContent                       SidebarContent       always
tree:Workbench.NavigationSidebar.SidebarContent.NavigationTreeView    NavigationTreeView   standard
tree:Workbench.NavigationSidebar.SidebarContent.ObjectTreeView        ObjectTreeView       dev
tree:Workbench.NavigationSidebar.SidebarFooter                        SidebarFooter        always
tree:Workbench.NavigationSidebar.SidebarFooter.LoginControl           LoginControl         always
tree:Workbench.NavigationSidebar.SidebarFooter.UserProfileControl     UserProfileControl   always
tree:Workbench.NavigationSidebar.SidebarFooter.DevModeToggle          DevModeToggle        always*
tree:Workbench.ContentPanel                                           ContentPanel         always
tree:Workbench.ContentPanel.ObjectEditor                              ObjectEditor         dev

* DevModeToggle only renders when user has ROLE_SERVICE_ADMIN (server-pruned).

Standard mode: NavigationTreeView active, ContentPanel renders CMS page resolved by route.
Dev mode:      ObjectTreeView active, ContentPanel renders ObjectEditor for selected tree node.
```

```
RPC bindings:
  NavigationTreeView → rpc_operation: "readNavigationRoutes", rpc_contract: "ReadNavigationRoutesResult1"
  ObjectTreeView     → rpc_operation: "readObjectTree",       rpc_contract: "ReadObjectTreeResult1"
  ObjectEditor       → rpc_operation: "readObjectDetail",     rpc_contract: "ReadObjectDetailResult1"
  LoginControl       → rpc_operation: "getAuthState"
  UserProfileControl → rpc_operation: "readCurrentUser"
```

**Total: 13 tree nodes for the Workbench shell. All deterministic — same GUID in every database instance.**

---

## 5. Seed Data: Routes

All deterministic UUID5 from `uuid5(NS, 'route:{path}')`.

The Workbench itself is NOT a route — it's the app shell. Routes define what renders *inside* the ContentPanel in standard mode.

**Every route must have a `ref_root_node_guid`.** Routes are only registered once their page component tree is fully defined. No placeholders, no stubs pointing to the Workbench root.

### Initial seed: Homepage only

| pub_path | pub_title | pub_icon | pub_sequence | ref_required_role_guid |
|---|---|---|---|---|
| `/` | Home | Home | 10 | *(null — public)* |

**Total: 1 route.**

Additional routes are registered as their page component trees are built through the CMS engine. The full set of routes from the existing page specs (gallery, products, profile, system admin pages, finance pages, etc.) will each get their own tree definition and route registration in future passes.

---

## 6. Object Tree Registration

All four new tables must be registered in the object tree (self-describing):

### Tables to register in `system_objects_database_tables`:

```
uuid5(NS, 'table:system_objects_components')      → system_objects_components
uuid5(NS, 'table:system_objects_component_tree')   → system_objects_component_tree
uuid5(NS, 'table:system_objects_routes')           → system_objects_routes
uuid5(NS, 'table:system_objects_type_controls')    → system_objects_type_controls
```

### Columns to register in `system_objects_database_columns`:

Each column of each new table needs a deterministic UUID5 entry:
```
uuid5(NS, 'column:{table_name}.{column_name}')
```

### Indexes and constraints follow the same pattern.

This is mechanical — the migration script generates all the INSERT statements. The column registrations reference the type GUIDs that already exist in `system_objects_types`.

---

## 7. Migration Script Structure

The migration `v0.12.3.0_cms_engine_foundation.sql` should execute in this order:

```
1. INSERT DECIMAL_28_12 into system_objects_types
2. CREATE TABLE system_objects_components
3. CREATE TABLE system_objects_component_tree
4. CREATE TABLE system_objects_routes
5. CREATE TABLE system_objects_type_controls
6. SEED component registry (42 rows)
7. SEED type-to-control default mappings (12 rows)
8. SEED Workbench component tree (12 tree nodes)
9. SEED initial routes (17 rows)
10. REGISTER new tables in system_objects_database_tables (4 rows)
11. REGISTER new columns in system_objects_database_columns (~30+ rows)
12. REGISTER new indexes in system_objects_database_indexes
13. REGISTER new constraints in system_objects_database_constraints
14. Verification queries
```

---

## 8. RPC Surface Required

New RPC operations needed for the Workbench (these are implementation targets, not seeded — they'll be built in the server modules):

### Navigation Domain (likely `public` or new `navigation` subdomain)

- `readNavigationRoutes` — returns hierarchical route tree pruned by user roles
- `resolveRoute` — maps a path to a root component tree node GUID

### Object Tree Domain (likely `system` or new `objects` subdomain)

- `readObjectTree` — returns one level of the object tree (lazy load)
- `readObjectDetail` — returns editable fields for a specific object
- `updateObjectField` — per-field mutation for an object
- `createObjectTreeNode` — creates a new object in the tree
- `deleteObjectTreeNode` — deletes an object and cascades children

### CMS Rendering Domain (likely new `cms` subdomain)

- `loadPageComponents` — returns security-pruned component tree for a page

### Auth Domain (existing `auth` subdomain, may need extension)

- `getAuthState` — returns auth state and available providers
- `readCurrentUser` — returns current user profile with roles/entitlements/has_dev_access

---

## 9. Summary: What Gets Created

| Category | Count | Key Strategy | Notes |
|---|---|---|---|
| New types | 1 | Deterministic: `uuid5(NS, 'type:DECIMAL_28_12')` | Added back |
| New tables | 4 | Deterministic: `uuid5(NS, 'table:{name}')` | components, component_tree, routes, type_controls |
| Component registrations | 21 | Deterministic: `uuid5(NS, 'component:{name}')` | 1 page + 9 section + 11 control (Workbench-only) |
| Type-to-control mappings | 12 | Deterministic: `uuid5(NS, 'typecontrol:{type}.{component}')` | One default per type |
| Workbench tree nodes | 13 | Deterministic: `uuid5(NS, 'tree:{full.path}')` | App shell definition incl. ObjectEditor |
| Route registrations | 1 | Deterministic: `uuid5(NS, 'route:{path}')` | Homepage only — others added as page trees are defined |
| Object tree registrations | 4 tables + ~37 columns + indexes + constraints | Deterministic: existing patterns | Self-describing |
| New RPC operations | ~9 | *(n/a — code, not data)* | Navigation, object tree, CMS, auth |

**Every GUID in every seed row is deterministic.** Same seed script run against any database instance produces identical GUIDs. No drift between environments.

**Next step:** Define the server module API surface — Pydantic models, RPC operations, and query registry entries for the 4 new tables. This unlocks the seed data population and the Codex implementation work.