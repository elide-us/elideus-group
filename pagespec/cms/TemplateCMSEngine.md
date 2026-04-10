# Template CMS Engine

**Scope:** Platform architecture spec — Layers 1–3 only. Defines the unified system through which all pages are expressed: what they show, what components render them, and what RPC function contracts feed them.

*This spec does not define database tables, Python models, or SQL. It defines the front-end data contract: the TypeScript-level shapes the client consumes, and the abstract component pattern that all pages conform to.*

*This system builds into the `system_objects_*` tree — the universal self-describing registry for all application elements. The object tree already describes types, database tables, columns, indexes, and constraints. The CMS engine extends it to also describe page components, their composition hierarchy, and their data bindings.*

---

## 1. Design Intent

Every page in the Oracle platform shows data that comes from RPC function calls. Every page spec already defines those function calls and their TypeScript input/output shapes. What varies between pages is the *arrangement* — how those fields are laid out, what controls render them, and what interactions are available.

The Template CMS Engine unifies that arrangement into a single recursive pattern. Instead of each page being a bespoke React component that hardcodes its layout, every page is expressed as a **component tree** — a recursive structure of containers and controls where:

- Each container defines a layout pattern (summary bar, sortable grid, collapsible section, tabs, feed, etc.)
- Each leaf control binds to a specific field from a specific RPC response contract
- The RPC security layer determines per-user what renders and whether it's editable
- The entire tree is data-driven — page structure is configuration, not code

The component catalog is code. The component *composition* is data. New component types require code changes. New pages, new field arrangements, and new data bindings do not.

---

## 2. Core Abstraction: Everything Is a Component

There is no distinction between "template," "page," "section," and "control." They are all components. A component is recursive — it can contain other components (container) or render a bound value (leaf).

```
Component
├── Contains other Components (container role)
│   Examples: SummaryAndGridPage, CollapsibleSection, SortableGrid, TabSection
└── Renders a bound value (leaf role)
    Examples: StringControl, DecimalControl, BoolToggle, DropdownSelect, ButtonAction
```

A "page" is the root component. A "template" is a reusable component pattern. A "field" is a leaf component bound to a value from an RPC response. The tree recurses arbitrarily.

### Component Categories

| Category | Role | Examples |
|---|---|---|
| **Page** | Root-level layout. Entry point for a route. | `SummaryAndGridPage`, `HeaderDetailPage`, `StaticContentPage`, `TabbedPage`, `FeedPage` |
| **Section** | Structural container within a page. | `CollapsibleSection`, `TabSection`, `CardSection`, `FormSection` |
| **Grid** | Tabular data container with built-in filter/sort/pagination. | `SortableGrid`, `ReadOnlyGrid`, `EditableGrid` |
| **Control** | Leaf-level data renderer/editor. Binds to a single field from an RPC response. | `StringControl`, `DecimalControl`, `BoolToggle`, `DropdownSelect`, `MultiSelect`, `DatePicker`, `ButtonAction`, `SliderControl`, `MarkdownEditor`, `ImageUpload`, `ReadOnlyDisplay`, `LinkControl`, `ChipList` |

### EDT-to-Control Relationship

Each control has a natural affinity to one or more types from `system_objects_types`. The v0.12 type registry includes Python, TypeScript, and JSON type mappings alongside database types, which means type metadata is available at every layer of the stack. The type of a bound field determines the **default** control, but the component tree can override it. For example, a `STRING` field defaults to `StringControl`, but in a specific component tree it might be rendered as a `DropdownSelect` (when the field's values come from a lookup) or a `LinkControl` (when the field is a URL).

Current type registry (from `system_objects_types`):

| pub_name | pub_typescript_type | pub_python_type | pub_mssql_type | Default Control |
|---|---|---|---|---|
| INT32 | number | int | int | `IntControl` |
| INT64 | number | int | bigint | `IntControl` |
| INT64_IDENTITY | number | int | bigint identity(1,1) | `ReadOnlyDisplay` |
| UUID | string | str | uniqueidentifier | `ReadOnlyDisplay` |
| BOOL | boolean | bool | bit | `BoolToggle` |
| DATETIME_TZ | string | str | datetimeoffset(7) | `DatePicker` |
| STRING | string | str | nvarchar | `StringControl` |
| TEXT | string | str | nvarchar(max) | `TextAreaControl` |
| INT8 | number | int | tinyint | `IntControl` |
| DATE | string | str | date | `DatePicker` |
| DECIMAL_19_5 | number | float | decimal(19,5) | `DecimalControl` |

---

## 3. Page Load Lifecycle

### Step 1: Route Resolution

The user navigates to a route (e.g., `/user-manager`). The application resolves this route to a root component definition. The root component definition identifies:

- The root component type (e.g., `SummaryAndGridPage`)
- The RPC operation(s) that provide data for this page
- The child component tree

### Step 2: Security-Pruned Tree Load

The client requests the component tree for this route. The server evaluates the current user's roles and entitlements against every node in the tree. The response contains **only the nodes this user is allowed to see**. Nodes the user cannot access are omitted entirely — not returned with a "hidden" flag.

For nodes the user can see, the response includes the **disposition** of each control for this user: editable or read-only, active or inactive, enabled or disabled. The same tree definition serves different roles: an admin sees editable fields with active action buttons; a viewer sees read-only fields with action buttons omitted; an unauthenticated user sees nothing. All of this is determined by the server — the client renders exactly what it receives.

### Step 3: Contract Extraction and Data Loading

Each node in the tree that has an `rpc_operation` fires that RPC call to load its data. The RPC response is a contract — a TypeScript shape as defined in the relevant page spec (e.g., `ReadUserHeaderList1`, `ReadConfigList1`). The component extracts its bound field from the response and renders it.

Container components distribute their RPC response to their children. A `SortableGrid` bound to `readUserHeaders` loads `ReadUserHeaderList1` and renders a row per element, where each column is a leaf control bound to a field within `ReadUserHeaderElement1`.

### Step 4: Mutation Dispatch

Each editable leaf control dispatches its own RPC mutation call when the user commits a change:

- **StringControl** → dispatches on tab-out / blur
- **BoolToggle** → dispatches on toggle / check
- **DropdownSelect** → dispatches on selection
- **DecimalControl** → dispatches on tab-out / blur
- **ButtonAction** → dispatches on click
- **EditableGrid rows** → dispatch on row-level `+` (insert), tab-out (update), or `×` (delete)

The mutation function name and its request shape are part of the component node's configuration. This matches the existing per-control dispatch pattern — there is no form-level "save all."

**Batch operations** follow the same pattern at a different granularity: a grid in multi-select mode collects selected row keys, and a `ButtonAction` dispatches a batch mutation RPC call with an input shape that accepts multiple keys (e.g., `{ guids: string[] }`). Atomicity is enforced by the server module — the client only collects and sends. All-or-nothing execution, rollback, and error handling are server-side concerns.

---

## 4. How Existing Page Specs Map to This Pattern

Every existing page spec defines: (1) what the page does, (2) what functions load its data, (3) the TypeScript shapes of those functions. The CMS engine doesn't replace those specs — it provides a **uniform structure** for rendering them.

### Example: SystemConfigPage

The existing spec defines:

- `readConfig` → `ReadConfigList1` → `{ elements: ReadConfigElement1[] }`
- `ReadConfigElement1` → `{ guid: string, key: string, value: string }`
- `createConfig`, `updateConfig`, `deleteConfig` — mutation functions

In the CMS model, this page is:

```
SummaryAndGridPage (root)
└── EditableGrid
    ├── rpc_operation: "readConfig"
    ├── rpc_contract: "ReadConfigList1"
    ├── children (column definitions):
    │   ├── StringControl(field: "key", label: "Key", editable: true)
    │   ├── StringControl(field: "value", label: "Value", editable: true)
    │   └── ButtonAction(label: "Delete", mutation: "deleteConfig", params: { guid: "{row.guid}" })
    ├── insert_mutation: "createConfig"
    └── update_mutation: "updateConfig"
```

The page spec doesn't change. The CMS engine just describes *how the spec's contracts map to visual components.*

### Example: SystemUserManager

The existing spec defines a summary + headers + detail pattern:

```
SummaryAndGridPage (root)
├── FormSection (summary)
│   ├── rpc_operation: "readUserSummary"
│   ├── rpc_contract: "ReadUserSummaryResult1"
│   ├── IntControl(field: "total_users", label: "Total Users")
│   ├── IntControl(field: "storage_enabled_count", label: "Storage Enabled")
│   ├── IntControl(field: "total_credits", label: "Total Credits")
│   └── IntControl(field: "active_sessions", label: "Active Sessions")
└── SortableGrid (headers)
    ├── rpc_operation: "readUserHeaders"
    ├── rpc_contract: "ReadUserHeaderList1"
    ├── columns:
    │   ├── StringControl(field: "display_name")
    │   ├── StringControl(field: "public_id")
    │   ├── StringControl(field: "email")
    │   ├── StringControl(field: "provider_name")
    │   ├── IntControl(field: "credits")
    │   ├── IntControl(field: "role_count")
    │   └── BoolToggle(field: "is_storage_enabled")
    └── onRowClick → HeaderDetailPage
        ├── rpc_operation: "readUserDetail"
        ├── rpc_contract: "ReadUserDetailResult1"
        ├── FormSection (identity)
        │   ├── StringControl(field: "display_name", editable: false)
        │   ├── StringControl(field: "public_id", editable: false)
        │   ├── StringControl(field: "email", editable: false)
        │   └── BoolToggle(field: "optin", editable: false)
        ├── FormSection (administration)
        │   ├── IntControl(field: "credits", editable: true, mutation: "setUserCredits")
        │   ├── ChipList(field: "roles", editable: false)
        │   ├── ButtonAction(label: "Assign Role", mutation: "assignUserRole")
        │   ├── ButtonAction(label: "Remove Role", mutation: "removeUserRole")
        │   └── ButtonAction(label: "Reset Display Name", mutation: "resetUserDisplay")
        └── FormSection (storage)
            └── ButtonAction(label: "Create Storage Folder", mutation: "createUserStorageFolder")
```

### Example: StaticContentPage (Content Pages / Wiki)

```
StaticContentPage (root)
├── rpc_operation: "readPageBySlug"
├── rpc_contract: "ReadPageBySlugResult1"
└── MarkdownEditor(field: "content", editable: [role-dependent])
```

### Pattern Summary

| Page Spec Pattern | CMS Root Component | Key RPC Contracts |
|---|---|---|
| Simple CRUD table | `EditableGrid` (or `SummaryAndGridPage` wrapping one) | `readX` → list, `createX`, `updateX`, `deleteX` |
| Summary + Header Grid | `SummaryAndGridPage` | `readXSummary` → summary, `readXHeaders` → paginated list |
| Summary + Headers + Detail | `SummaryAndGridPage` → drill to `HeaderDetailPage` | Above + `readXDetail` → single record |
| Static content | `StaticContentPage` | `readPageBySlug` → markdown blob |
| Feed | `FeedPage` | `readFeed` → paginated card list |

---

## 5. Component Tree Data Contract

The following TypeScript types define the shape of the component tree as consumed by the front-end rendering engine. This is the contract between the server (which builds and security-prunes the tree) and the client (which renders it).

### Component Registration

```typescript
/**
 * A registered component type in the catalog.
 * Code-defined, referenced by tree nodes.
 * key_guid: deterministic UUID5 from uuid5(NS, 'component:{name}')
 * ref_type_guid: FK to system_objects_types for default EDT binding (nullable for containers)
 */
interface ComponentRegistration {
  key_guid: string;
  pub_name: string;              // e.g., "SortableGrid", "StringControl"
  pub_category: string;          // "page" | "section" | "grid" | "control"
  pub_description: string | null;
  default_type_name: string | null; // Denormalized from system_objects_types join
}
```

### Component Tree Node

```typescript
/**
 * A single node in the component tree. Recursive via children.
 * key_guid: random (instance data, not canonical definitions)
 * ref_parent_guid: self-referential FK (null for root nodes)
 * ref_component_guid: FK to ComponentRegistration
 * ref_type_guid: FK to system_objects_types (override for leaf controls, nullable)
 */
interface ComponentTreeNode {
  key_guid: string;
  component_name: string;        // Denormalized from ComponentRegistration
  pub_category: string;          // Denormalized from registration
  pub_label: string | null;      // Display label (column header, section title, field label)
  pub_field_binding: string | null; // Field name within the RPC response this leaf binds to
  pub_sequence: number;          // Render order within parent
  pub_rpc_operation: string | null;  // RPC function name for data loading (containers)
  pub_rpc_contract: string | null;   // TypeScript type name of the expected response
  pub_mutation_operation: string | null; // RPC function name for writes (leaf controls)
  editable: boolean;             // Resolved per-user by security pruning
  children: ComponentTreeNode[]; // Recursive child components
}
```

### Runtime (Security-Pruned) Tree

```typescript
/** The tree as returned by loadPageComponents — already pruned for this user. */
interface RuntimePageTree {
  route: string;
  root: ComponentTreeNode;  // Only contains nodes this user can see
}
```

### Type-to-Control Mapping

```typescript
/**
 * Maps a type from system_objects_types to a rendering control. Many-to-many.
 * Replaces the legacy EDT-to-control concept with a formal FK relationship.
 */
interface TypeControlMapping {
  key_guid: string;
  type_name: string;          // Denormalized from system_objects_types (e.g., "STRING", "DECIMAL_19_5")
  component_name: string;    // Denormalized from ComponentRegistration (e.g., "StringControl")
  pub_is_default: boolean;   // Default control for this type
}
```

---

## 6. RPC Function Surface

These are the RPC functions the CMS engine requires. They follow the same pattern as all other page spec function definitions.

### Page Resolution and Rendering

#### `resolveRoute`

- **Request:** `ResolveRouteParams1` — `{ path: string }`
- **Response:** `ResolveRouteResult1` — `{ root_guid: string, component_name: string }`

*Given a route path, returns the root component GUID and type name for that page.*

#### `loadPageComponents`

- **Request:** `LoadPageComponentsParams1` — `{ root_guid: string }`
- **Response:** `LoadPageComponentsResult1` — `{ route: string, root: ComponentTreeNode }`

*Primary runtime function. Returns the full component tree for a page, pre-pruned for the current user's security context. Nodes where the user has no access are excluded. The `editable` flag on each node reflects this user's actual permission, not a default.*

### Component Registry Management

#### `readComponentRegistry`

- **Request:** none
- **Response:** `ReadComponentRegistryResult1` — `{ elements: ComponentRegistrationElement1[] }`
- `ComponentRegistrationElement1` — `{ key_guid: string, pub_name: string, pub_category: string, pub_description: string | null, default_type_name: string | null }`

#### `createComponentRegistration`

- **Request:** `CreateComponentRegistrationParams1` — `{ pub_name: string, pub_category: string, pub_description: string | null }`
- **Response:** `CreateComponentRegistrationResult1` — `{ key_guid: string, pub_name: string, pub_category: string }`

#### `deleteComponentRegistration`

- **Request:** `DeleteComponentRegistrationParams1` — `{ key_guid: string }`
- **Response:** `DeleteComponentRegistrationResult1` — `{ key_guid: string }`

### Component Tree Management (Builder)

#### `readComponentTree`

- **Request:** `ReadComponentTreeParams1` — `{ root_guid: string }`
- **Response:** `ReadComponentTreeResult1` — `{ root: ComponentTreeNode }`

*Returns the full tree without security pruning. Used by the page builder, not by the rendering engine.*

#### `createComponentTreeNode`

- **Request:** `CreateComponentTreeNodeParams1` — `{ ref_parent_guid: string | null, pub_component_name: string, pub_label: string | null, pub_field_binding: string | null, pub_sequence: int, pub_rpc_operation: string | null, pub_rpc_contract: string | null, pub_mutation_operation: string | null }`
- **Response:** `CreateComponentTreeNodeResult1` — `{ key_guid: string, component_name: string, pub_label: string | null, pub_sequence: int }`

#### `updateComponentTreeNode`

- **Request:** `UpdateComponentTreeNodeParams1` — `{ key_guid: string, pub_label: string | null, pub_field_binding: string | null, pub_sequence: int, pub_rpc_operation: string | null, pub_rpc_contract: string | null, pub_mutation_operation: string | null }`
- **Response:** `UpdateComponentTreeNodeResult1` — `{ key_guid: string }`

#### `deleteComponentTreeNode`

- **Request:** `DeleteComponentTreeNodeParams1` — `{ key_guid: string }`
- **Response:** `DeleteComponentTreeNodeResult1` — `{ key_guid: string, children_deleted: int }`

*Cascade deletes all descendant nodes.*

#### `moveComponentTreeNode`

- **Request:** `MoveComponentTreeNodeParams1` — `{ key_guid: string, ref_new_parent_guid: string | null, pub_new_sequence: int }`
- **Response:** `MoveComponentTreeNodeResult1` — `{ key_guid: string, ref_parent_guid: string | null, pub_sequence: int }`

### Type-to-Control Mapping Management

#### `readTypeControlMappings`

- **Request:** none
- **Response:** `ReadTypeControlMappingList1` — `{ elements: TypeControlMappingElement1[] }`
- `TypeControlMappingElement1` — `{ key_guid: string, type_name: string, component_name: string, pub_is_default: bool }`

#### `createTypeControlMapping`

- **Request:** `CreateTypeControlMappingParams1` — `{ ref_type_guid: string, ref_component_guid: string, pub_is_default: bool }`
- **Response:** `CreateTypeControlMappingResult1` — `{ key_guid: string }`

#### `deleteTypeControlMapping`

- **Request:** `DeleteTypeControlMappingParams1` — `{ key_guid: string }`
- **Response:** `DeleteTypeControlMappingResult1` — `{ key_guid: string }`

---

## 7. Rendering Engine Contract

The React rendering engine is a single recursive component (`<CmsRenderer />`) that the application's router invokes for CMS-driven routes. Its contract with the rest of the application:

### Client-Side Component Registry

A static TypeScript map maintained in code. Every `component_name` referenced in a component tree must exist in this map. The map is the bridge between data-driven tree definitions and actual React implementations.

```typescript
interface CmsComponentProps {
  node: ComponentTreeNode;
  data: Record<string, unknown> | null;  // Data from parent's RPC response
  onMutate: (operation: string, params: Record<string, unknown>) => Promise<void>;
}

const COMPONENT_REGISTRY: Record<string, React.ComponentType<CmsComponentProps>> = {
  'SummaryAndGridPage': SummaryAndGridPage,
  'HeaderDetailPage': HeaderDetailPage,
  'StaticContentPage': StaticContentPage,
  'TabbedPage': TabbedPage,
  'FeedPage': FeedPage,
  'CollapsibleSection': CollapsibleSection,
  'TabSection': TabSection,
  'CardSection': CardSection,
  'FormSection': FormSection,
  'SortableGrid': SortableGrid,
  'ReadOnlyGrid': ReadOnlyGrid,
  'EditableGrid': EditableGrid,
  'StringControl': StringControl,
  'TextAreaControl': TextAreaControl,
  'MarkdownEditor': MarkdownEditor,
  'IntControl': IntControl,
  'DecimalControl': DecimalControl,
  'BoolToggle': BoolToggle,
  'DatePicker': DatePicker,
  'DropdownSelect': DropdownSelect,
  'MultiSelect': MultiSelect,
  'ButtonAction': ButtonAction,
  'SliderControl': SliderControl,
  'ImageUpload': ImageUpload,
  'ReadOnlyDisplay': ReadOnlyDisplay,
  'LinkControl': LinkControl,
  'ChipList': ChipList,
};
```

### Rendering Flow

```
1. Router matches route → calls resolveRoute(path)
2. resolveRoute returns root_guid
3. CmsRenderer calls loadPageComponents(root_guid)
4. Server returns security-pruned ComponentTreeNode tree
5. CmsRenderer looks up root node's component_name in COMPONENT_REGISTRY
6. Root component renders:
   a. If node has rpc_operation → call it, get data
   b. For each child in node.children (ordered by sequence):
      - Look up child.component_name in COMPONENT_REGISTRY
      - If container: pass data context, recurse
      - If leaf: extract data[child.field_binding], render control
   c. If leaf with mutation_operation → wire onChange/onBlur/onClick to dispatch mutation
7. Components whose rpc_operation returns access-denied → not rendered
```

### Data Context Propagation

When a container component loads data via its `rpc_operation`, it passes that data down to its children as context. Children bind to specific fields within that data. This avoids redundant RPC calls — a `SortableGrid` calls `readUserHeaders` once and distributes `display_name`, `email`, `credits`, etc., to its column controls.

For grid components specifically, the data context is per-row — each row in the grid gets its own data context from one element in the `elements` array of the list response. Each column control binds to a field within that row's element.

---

## 8. Component Catalog Detail

### Page Components

#### `SummaryAndGridPage`
The canonical list-view pattern. Contains a summary section (aggregate metrics) and a grid section (paginated list of records). Used by: SystemUserManager, SystemConversationsPage, and future list views.

- **Slots:** summary (FormSection or equivalent), grid (SortableGrid or equivalent)
- **OnLoad:** Delegates to children — summary section calls its own RPC operation, grid calls its own

#### `HeaderDetailPage`
The canonical record-view pattern. Shows header fields for a selected record with expandable detail sections below. Used by: user detail panel, conversation detail, and future record views.

- **Slots:** header (FormSection), detail sections (CollapsibleSection, FormSection, etc.)
- **OnLoad:** Single RPC operation at the page level, distributes fields to children
- **Context parameter:** Receives an identifier (e.g., `guid`, `thread_id`) from the navigation source (grid row click)

#### `StaticContentPage`
Renders a markdown blob. Used for content pages, wiki, privacy policy, ToS, changelogs.

- **Slots:** Single MarkdownEditor child
- **OnLoad:** Calls content-retrieval RPC (e.g., `readPageBySlug`)

#### `TabbedPage`
Multiple tab sections, one visible at a time. Each tab is a child container with its own data context.

- **Slots:** Ordered list of TabSection children
- **OnLoad:** Each tab loads its own data lazily on selection

#### `FeedPage`
Scrollable feed of cards with infinite scroll / pagination. Used for social feed, activity log, content posts.

- **Slots:** Repeating CardSection children, one per feed item
- **OnLoad:** Paginated RPC call, appends on scroll

### Section Components

#### `CollapsibleSection`
Expandable/collapsible container. Shows header label, expand arrow. Children render when expanded.

#### `TabSection`
Single panel within a TabbedPage. Renders its children when its tab is selected.

#### `CardSection`
Bordered card with optional header. Used as a repeated element in feeds or as a standalone grouping.

#### `FormSection`
Vertical stack of labeled controls. The standard layout for field groups within a detail view.

### Grid Components

#### `SortableGrid`
Full-featured grid with column sort, filter, pagination, row-click drill-in. Column definitions are child control nodes.

#### `ReadOnlyGrid`
Simplified grid — display only, no edit controls, no inline mutation. Sort and filter still available.

#### `EditableGrid`
Grid with inline editing: row-level edit mode (click to edit, tab-out to commit), add row control (`+`), delete row control (`×`).

### Control Components

All controls implement the `CmsComponentProps` interface. All controls render in two modes based on `node.editable`:

- **Editable mode:** Interactive control with mutation dispatch on commit
- **Read-only mode:** Display-only rendering of the bound value

Controls do not decide their own editability — the server decides, and the `editable` flag is set in the pruned tree.

---

## 9. Grid Column Definitions

Grid columns are defined as child nodes of the grid component in the component tree. Each child is a leaf control with:

- `field_binding` → the field name within each row element (e.g., `"display_name"`, `"credits"`)
- `label` → the column header text
- `component_name` → the control type for that column (e.g., `StringControl`, `IntControl`)
- `sequence` → column order

Additional column metadata:

```typescript
interface GridColumnProps {
  width: string | null;       // CSS width (e.g., "200px", "30%"), null for auto
  sortable: boolean;          // Whether this column supports sort
  filterable: boolean;        // Whether this column shows a filter control
  filter_type: string | null; // "text" | "numeric" | "date" | "bool" | "select" — derived from EDT if null
}
```

These properties are additional fields on the `ComponentTreeNode` when the parent is a grid component.

---

## 10. Dropdown and Lookup Data Sources

When a `DropdownSelect` or `MultiSelect` control needs to load its option list, it uses a **separate RPC operation** specified on the tree node. This is distinct from the parent's data-loading RPC operation.

The tree node for a dropdown includes:

- `rpc_operation` → the function that loads the dropdown options (e.g., `readModels`, `readRoles`)
- `rpc_contract` → the expected response shape (e.g., `ReadModelList1`)
- `field_binding` → the field in the *parent's* data context that this dropdown's selected value maps to
- `option_value_field` → which field in the dropdown's option list is the value (e.g., `"guid"`)
- `option_label_field` → which field in the dropdown's option list is the display label (e.g., `"name"`)

```typescript
interface DropdownProps {
  option_value_field: string;  // Field in options response to use as value
  option_label_field: string;  // Field in options response to use as display label
}
```

This allows any existing read-list RPC function to serve as a dropdown source without modification.

---

## 11. Navigation Between Pages

When a grid row click or a button action navigates to another page (e.g., from user headers to user detail), the navigation binding is expressed on the source component:

```typescript
interface NavigationBinding {
  target_route: string;           // Route pattern, e.g., "/user-manager/detail"
  target_root_guid: string;       // Root component GUID of the target page
  context_param: string;          // Field name from the current row to pass as context (e.g., "guid")
  context_param_name: string;     // Parameter name the target page expects (e.g., "guid")
}
```

The target page's root component receives the context parameter and passes it to its `rpc_operation` call.

---

## 12. Shared Data Contexts

When multiple sibling components on the same page need data from the same RPC call (e.g., a summary section and a grid both showing user data), the RPC operation is specified on their **common parent** container. The parent calls the RPC operation once and distributes the response to its children.

Children can also have their own `rpc_operation` for data that is specific to that component. The resolution order:

1. If a component has its own `rpc_operation`, it calls that and uses the response
2. If a component has no `rpc_operation`, it receives data from its parent's context
3. If a component has both, its own `rpc_operation` takes precedence

This prevents redundant RPC calls while allowing components to load their own data when needed.

---

## 13. Integration with the Object Tree

### The Object Tree as Universal Registry

The `system_objects_*` tables form a self-describing universal registry for all application elements. As of v0.12, this tree describes:

- **Types** (`system_objects_types`) — 11 data types with cross-platform type mappings (MSSQL, PostgreSQL, MySQL, Python, TypeScript, JSON)
- **Database tables** (`system_objects_database_tables`) — every table in the schema, GUID-keyed with deterministic UUID5
- **Database columns** (`system_objects_database_columns`) — every column, FK-linked to its table and its type
- **Database indexes** (`system_objects_database_indexes`) — index definitions FK-linked to tables
- **Database constraints** (`system_objects_database_constraints`) — FK constraint definitions with full referential links

The CMS engine extends this tree with new object categories for page components and their composition. The pattern is the same: deterministic UUID5 keys from the `DECAFBAD` namespace, self-describing metadata, FK relationships to types and to each other.

### New Object Tree Entries for CMS

The template system introduces new entries in the object tree following the existing `system_objects_*` pattern:

- **Component registrations** — registered component types (the code-defined catalog). Each entry follows the same `key_guid` / `pub_*` / `priv_*` / `ref_*` column convention. Components reference types via `ref_type_guid` FK to `system_objects_types` for their default EDT binding.
- **Component tree nodes** — the page composition hierarchy. Each node references its parent node (self-referential FK), its component registration, and optionally its bound type. Tree nodes are the CMS equivalent of what database columns are to database tables — they define the structure of a page the way columns define the structure of a table.
- **Route bindings** — maps a route path to a root component tree node. Replaces the legacy `frontend_pages` table.

### Column Naming Convention Alignment

All CMS tables follow the v0.12 column naming convention:

| Prefix | Purpose | Examples |
|---|---|---|
| `key_*` | Primary key (UNIQUEIDENTIFIER or BIGINT IDENTITY only) | `key_guid` |
| `pub_*` | Functional/public data — views, joins, API responses | `pub_name`, `pub_label`, `pub_sequence` |
| `priv_*` | Bookkeeping/audit | `priv_created_on`, `priv_modified_on` |
| `ref_*` | Foreign key references | `ref_parent_guid`, `ref_component_guid`, `ref_type_guid` |
| `ext_*` | Reserved for future extensions | *(not used yet)* |

### UUID5 Key Strategy

Component registration GUIDs are deterministic UUID5 from the application namespace:

```
uuid5(NS, 'component:{pub_name}')     → component registration GUID
uuid5(NS, 'page:{route_path}')        → route binding GUID
```

Component tree node GUIDs are random (not deterministic) — they represent instances, not definitions. This matches the pattern where `system_auth_roles` has deterministic GUIDs (role definitions are canonical) but `system_user_roles` has random GUIDs (role assignments are instance data).

### Security Integration

The v0.12 security model provides the foundation for CMS access control:

- **Roles** (`system_auth_roles`) — determine which components a user can see and whether they're editable. Each role has a `pub_rpc_domain` linking it to an RPC domain. The CMS tree pruning evaluates the user's roles against each node's required role.
- **Entitlements** (`system_auth_entitlements`) — determine feature-level access (e.g., `ENABLE_OPENAI_API` gates the AI generation controls). Entitlements can gate specific component tree nodes independently of roles.
- **Mapping tables** (`system_user_roles`, `system_user_entitlements`) — clean many-to-many joins on `ref_user_guid`. No bitmasks.

The `loadPageComponents` function joins the user's roles and entitlements to the component tree and prunes nodes the user cannot access. The same tree definition serves every role — the server-side pruning is the only security enforcement.

---

## 14. Migration Path

### Phase 1: Contract Definition (Current)
Extract page specs for all existing pages. Each spec defines the RPC function surface and TypeScript contracts. This is the current work — the specs are the source of truth for what data exists.

### Phase 2: Foundation Tables and Module API
Create the CMS engine tables (`system_objects_components`, `system_objects_component_tree`, `system_objects_routes`, `system_objects_type_controls`). Define the server module API surface — Pydantic models, RPC operations, query registry entries. Seed the component registry, type-to-control mappings, and the Workbench component tree.

### Phase 3: Workbench Implementation
Build the Workbench as the new application shell — NavigationSidebar, ContentPanel, CmsRenderer. This replaces `App.tsx` + `NavBar.tsx` + `<Outlet />` entirely. No legacy fallback. The Workbench is the application.

### Phase 4: Component Catalog Implementation
Build the leaf controls (`StringControl`, `DecimalControl`, etc.) and container components (`SortableGrid`, `FormSection`, etc.) as React components implementing `CmsComponentProps`.

### Phase 5: Page Tree Definitions
For each existing page spec, define its component tree in the database and register its route in `system_objects_routes`. Each page is built greenfield through the CMS engine — no static `.tsx` page files.

### Phase 6: Page Builder
Build the object tree editor (dev mode) as a CMS-driven page within the Workbench. This is the self-hosting milestone — the system defines itself through itself.

---

## 15. Design Constraints

1. **The client is a drawing surface.** The rendering engine does no logic beyond rendering logic. All business logic, validation, access control, state evaluation, and atomicity guarantees live in the server modules. The client renders what the server tells it to render, in the state the server specifies.

2. **The component catalog is finite and grows deliberately.** Adding a new component type (e.g., `ColorPickerControl`) requires a code change — a new React component and a registry entry. This is intentional. The set of available controls is curated and tested.

3. **No form-level save.** Each control dispatches its own mutations independently. Tab-out, toggle, selection, click — each control owns its writes. Batch operations are a specific pattern where a grid collects keys and a button dispatches a batch mutation RPC call.

4. **Security is exclusively server-side.** The component tree returned by `loadPageComponents` is already pruned. The client never evaluates access rules. If it's in the tree, render it. If it's marked editable, make it editable. If a button is returned as active, it's active.

5. **All control state is server-driven.** Active/inactive, enabled/disabled, visible/hidden — these are signals from the RPC response, not client-side evaluations. The component tree defines what *could* render; the RPC responses determine what *does* render and in what disposition.

6. **Validation is server-side.** The Pydantic model that defines the RPC input contract is the validation layer. The client enforces basic type matching through EDT-driven controls. Business validation is enforced by the server; invalid inputs return error responses that controls render as feedback.

7. **Page specs remain the source of truth for RPC contracts.** The CMS engine references RPC operation names and their TypeScript shapes as defined in page specs. The engine doesn't define new data — it defines how existing data is arranged visually.

8. **Types describe data, not components.** `system_objects_types` is consumed by the control mapping system to select default controls. Types are not extended to describe page structure, layout, or template patterns.

9. **Component tree nodes are GUID-keyed.** Tree node instances use random GUIDs (they represent instances, not definitions). Component registrations and route bindings use deterministic UUID5 from the application namespace (they represent canonical definitions). This matches the pattern in the security model where `system_auth_roles` GUIDs are deterministic but `system_user_roles` GUIDs are random.

10. **The tree is the page.** There are no separate "template" and "instance" concepts. Each page has one active component tree. Versioning tracks changes to that tree over time. Page trees are bespoke — no first-class template cloning mechanism. Patterns recur but each page owns its own tree.

---

## 16. Resolved Design Decisions

1. **Template reuse** — No special accommodation. Page trees are bespoke at this scale. Patterns will recur (many pages will use `SummaryAndGridPage` with similar structural arrangements), but each page defines its own tree with its own data bindings. If cloning is needed, it happens at the seed data level, not as a first-class platform feature.

2. **Conditional rendering** — All control state is server-driven. A button's active/inactive state, a checkbox's availability, a field's visibility — these are all signals returned by the RPC response. The rendering surface does **no logic beyond rendering logic**. If a button can link an account, the server returns it as active. If a user's name can be reset, the server returns the reset button as active. If a blog page can be published, the server returns the publish checkbox as enabled. The component tree defines what *could* render; the RPC responses determine what *does* render and in what state. No client-side conditional expressions.

3. **Batch operations** — Batch operations are RPC calls with input shapes that accept multiple keys. A `MultiSelect` grid mode collects selected row keys and passes them to a batch mutation operation (e.g., `batchDeleteJournals({ guids: string[] })`). The batch operation is atomic — all-or-nothing execution is enforced in the server module, not the client. The grid component provides the selection UI; the `ButtonAction` bound to the batch mutation operation dispatches the call with the collected keys. All atomicity guarantees are server-side concerns.

4. **Validation rules** — Validation is server-side. The Pydantic model that defines the RPC input contract is the validation layer. The TypeScript interface published from that model is the client's contract. The client enforces basic type matching (you can't put a string in an int field) through the EDT-driven control type, but business validation (required fields, range constraints, format rules, referential integrity) is enforced by the server when the mutation RPC call is dispatched. Invalid inputs return error responses that the control renders as validation feedback. No client-side validation rules are stored in the component tree.
