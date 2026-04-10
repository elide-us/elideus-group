# Workbench Template

**Scope:** Platform page spec — the root application shell. Replaces the current `App.tsx` + `NavBar.tsx` + `<Outlet />` pattern with a CMS-driven workbench layout.

*This is the first component expressed through the Template CMS Engine. Every other page renders inside it. The workbench defines the outer frame — navigation sidebar and content panel — and the content panel hosts whatever page the current route resolves to via the CMS engine.*

---

## 1. UX Spec

### Layout

The workbench is a two-panel horizontal layout that fills the viewport:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Workbench                                                           │
│ ┌──────────────┬────────────────────────────────────────────────────┐│
│ │ Navigation   │ Content Panel                                     ││
│ │ Sidebar      │                                                   ││
│ │              │ [Rendered page based on current route              ││
│ │ ┌──────────┐ │  or object editor based on tree selection]        ││
│ │ │ Sidebar  │ │                                                   ││
│ │ │ Header   │ │                                                   ││
│ │ │ [☰]      │ │                                                   ││
│ │ ├──────────┤ │                                                   ││
│ │ │ Sidebar  │ │                                                   ││
│ │ │ Content  │ │                                                   ││
│ │ │          │ │                                                   ││
│ │ │ [Routes] │ │                                                   ││
│ │ │  or      │ │                                                   ││
│ │ │ [Object  │ │                                                   ││
│ │ │  Tree]   │ │                                                   ││
│ │ │          │ │                                                   ││
│ │ ├──────────┤ │                                                   ││
│ │ │ Sidebar  │ │                                                   ││
│ │ │ Footer   │ │                                                   ││
│ │ │ [Login]  │ │                                                   ││
│ │ │ [User]   │ │                                                   ││
│ │ │ [Dev ⚙]  │ │                                                   ││
│ │ └──────────┘ │                                                   ││
│ └──────────────┴────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Navigation Sidebar

The sidebar is a vertical panel on the left edge of the viewport. It has three vertical sections:

#### Sidebar Header

Contains the **hamburger toggle** — a button that expands/collapses the sidebar drawer between its narrow (icon-only) and wide (icon + label) states. This is the existing `MenuIcon` toggle behavior from the current NavBar.

When collapsed, the sidebar shows only icons. When expanded, it shows icons with text labels. The toggle animates the width transition.

#### Sidebar Content

The scrollable middle section. Its content depends on the current mode:

**Standard Mode (default):**
Displays a **NavigationTreeView** — a hierarchical tree of navigable routes. Each route item is role-masked (the server only returns routes the user is entitled to see). Route items are grouped into sections (by sequence bucket, as in the current NavBar). Clicking a route item navigates the ContentPanel to that route's page.

The tree view supports nested items — a route group can expand to show child routes. This replaces the current flat list with a hierarchical navigation structure that can accommodate growing page counts.

**Dev Mode:**
Displays the **ObjectTreeView** — a live, editable view of the `system_objects_*` tree. This is the IDE view. The tree shows:

- Types (`system_objects_types`)
- Database Tables → Columns, Indexes, Constraints (`system_objects_database_*`)
- Component Registrations (future — CMS engine components)
- Component Trees / Page Definitions (future — CMS page structures)
- Roles and Entitlements (`system_auth_roles`, `system_auth_entitlements`)

Each node in the object tree is clickable. Clicking a node loads its **object editor** in the ContentPanel — a form view appropriate to the object type (type editor, table editor with column grid, component registration editor, etc.).

The object tree is lazy-loaded — top-level categories load on mode switch, children load on expand.

#### Sidebar Footer

Pinned to the bottom of the sidebar. Contains:

- **LoginControl** — the existing authentication widget (login button when unauthenticated, user info when authenticated)
- **UserProfileControl** — avatar, display name, logout action (when authenticated)
- **DevModeToggle** — a toggle or button that switches the SidebarContent between Standard Mode (route navigation) and Dev Mode (object tree). Only visible to users with `ROLE_SERVICE_ADMIN`.

### Content Panel

The main content area. Fills the remaining horizontal space to the right of the sidebar. Renders content based on the current context:

**In Standard Mode:** Renders the CMS-driven page resolved by the current route. The CMS engine's `resolveRoute` → `loadPageComponents` → `CmsRenderer` pipeline renders the page here. This replaces the current React Router `<Outlet />`.

**In Dev Mode:** Renders the object editor for whatever node is currently selected in the ObjectTreeView. The editor is itself a CMS-driven page — the object tree is its own page definition in the CMS engine, with editors for each object type.

---

## 2. Component Tree (CMS Definition)

```
Workbench (root, category: page)                                          mode: always
├── NavigationSidebar (category: section)                                 mode: always
│   ├── SidebarHeader (category: section)                                 mode: always
│   │   └── HamburgerToggle (category: control)                           mode: always
│   ├── SidebarContent (category: section)                                mode: always
│   │   ├── NavigationTreeView (category: section)                        mode: standard
│   │   │   ├── rpc_operation: "readNavigationRoutes"
│   │   │   ├── rpc_contract: "ReadNavigationRoutesResult1"
│   │   │   └── NavigationItem[] (category: control)
│   │   │       └── field_binding: "path", "name", "icon", "sequence"
│   │   └── ObjectTreeView (category: section)                            mode: dev
│   │       ├── rpc_operation: "readObjectTree"
│   │       ├── rpc_contract: "ReadObjectTreeResult1"
│   │       └── ObjectTreeNode[] (category: control)
│   │           └── field_binding: "key_guid", "pub_name", "object_type"
│   └── SidebarFooter (category: section)                                 mode: always
│       ├── LoginControl (category: control)                              mode: always
│       │   └── rpc_operation: "getAuthState"
│       ├── UserProfileControl (category: control)                        mode: always
│       │   └── rpc_operation: "readCurrentUser"
│       └── DevModeToggle (category: control)                             ROLE_SERVICE_ADMIN only
└── ContentPanel (category: section)                                      mode: always
    └── ObjectEditor (category: section)                                  mode: dev
        ├── rpc_operation: "readObjectDetail"
        ├── rpc_contract: "ReadObjectDetailResult1"
        └── [typed controls rendered from object field definitions]

Standard mode: NavigationTreeView active in sidebar, ContentPanel renders CMS page by route.
Dev mode:      ObjectTreeView active in sidebar, ContentPanel renders ObjectEditor for selected node.
```

---

## 3. Data Requirements

### Standard Mode: Navigation Routes

#### `readNavigationRoutes`

- **Request:** none (authenticated user context — server prunes by role)
- **Response:** `ReadNavigationRoutesResult1` — `{ elements: NavigationRouteElement1[] }`
- `NavigationRouteElement1` — `{ path: string, name: string, icon: string, sequence: number, parent_path: string | null, children: NavigationRouteElement1[] }`

*Returns the hierarchical route tree for the current user. Routes the user cannot access are omitted. `parent_path` enables tree nesting. `icon` is a Material icon name (resolved client-side via the existing `DynamicIcon` component). `sequence` controls display order within each level.*

*This replaces the current `fetchNavbarRoutes` call from `rpc/public/links`. The response shape changes from a flat list to a recursive tree.*

### Dev Mode: Object Tree

#### `readObjectTree`

- **Request:** `ReadObjectTreeParams1` — `{ parent_guid: string | null }`
- **Response:** `ReadObjectTreeResult1` — `{ elements: ObjectTreeElement1[] }`
- `ObjectTreeElement1` — `{ key_guid: string, pub_name: string, object_type: string, object_category: string, has_children: bool }`

*Returns one level of the object tree. When `parent_guid` is null, returns top-level categories (Types, Tables, Components, Roles, etc.). When `parent_guid` is a specific object GUID, returns its children (e.g., columns for a table, fields for a component). Lazy-loaded — the tree expands one level at a time.*

*`object_type` identifies what kind of object this is: `"type"`, `"table"`, `"column"`, `"index"`, `"constraint"`, `"component"`, `"tree_node"`, `"role"`, `"entitlement"`. `object_category` is a grouping label (e.g., `"Database"`, `"CMS"`, `"Security"`).*

#### `readObjectDetail`

- **Request:** `ReadObjectDetailParams1` — `{ key_guid: string, object_type: string }`
- **Response:** `ReadObjectDetailResult1` — `{ object_type: string, fields: ObjectFieldElement1[] }`
- `ObjectFieldElement1` — `{ pub_name: string, type_name: string, value: string | number | boolean | null, editable: bool }`

*Returns the editable fields for a specific object in the tree. The ContentPanel renders these as a form (FormSection with typed controls). `type_name` maps to `system_objects_types.pub_name` and determines which control renders the field. `editable` is resolved per-user by the RPC security layer.*

#### `updateObjectField`

- **Request:** `UpdateObjectFieldParams1` — `{ key_guid: string, object_type: string, field_name: string, value: string | number | boolean | null }`
- **Response:** `UpdateObjectFieldResult1` — `{ key_guid: string, field_name: string, value: string | number | boolean | null }`

*Per-field mutation. Dispatched on tab-out/blur from an editable control in the object editor. Follows the standard per-control dispatch pattern.*

#### `createObjectTreeNode`

- **Request:** `CreateObjectTreeNodeParams1` — `{ parent_guid: string, object_type: string, pub_name: string }`
- **Response:** `CreateObjectTreeNodeResult1` — `{ key_guid: string, pub_name: string, object_type: string }`

*Creates a new object as a child of an existing tree node. Used by the `+` control in the object tree view.*

#### `deleteObjectTreeNode`

- **Request:** `DeleteObjectTreeNodeParams1` — `{ key_guid: string, object_type: string }`
- **Response:** `DeleteObjectTreeNodeResult1` — `{ key_guid: string, children_deleted: int }`

*Deletes an object and cascades to its children. Used by the `×` control in the object tree view.*

### Sidebar Footer: Auth and User State

#### `getAuthState`

- **Request:** none
- **Response:** `GetAuthStateResult1` — `{ is_authenticated: bool, providers: AuthProviderElement1[] }`
- `AuthProviderElement1` — `{ key_guid: string, pub_name: string, pub_display: string, pub_sequence: number }`

*Returns authentication state and available providers for the login widget. Providers are loaded from `service_auth_providers`.*

#### `readCurrentUser`

- **Request:** none (from bearer token)
- **Response:** `ReadCurrentUserResult1` — `{ key_guid: string, pub_display: string, pub_email: string, roles: string[], entitlements: string[], has_dev_access: bool }`

*Returns the current user's profile and security context. `has_dev_access` is derived from role membership (`ROLE_SERVICE_ADMIN`) and determines whether the DevModeToggle is visible.*

---

## 4. New Components Required

These are components that must be added to the client-side component registry for the workbench. They do not exist in the current component catalog.

| Component | Category | Description |
|---|---|---|
| `Workbench` | page | Root shell. Renders NavigationSidebar and ContentPanel side by side. Manages mode state (standard/dev) and sidebar expanded/collapsed state. |
| `NavigationSidebar` | section | Vertical panel with three slots (header, content, footer). Manages width animation. |
| `SidebarHeader` | section | Top-pinned container within the sidebar. |
| `SidebarContent` | section | Scrollable middle container. Renders NavigationTreeView (standard) or ObjectTreeView (dev) based on mode. |
| `SidebarFooter` | section | Bottom-pinned container within the sidebar. |
| `NavigationTreeView` | section | Renders a hierarchical tree of navigable routes from `readNavigationRoutes`. Supports nested items with expand/collapse. Standard mode. |
| `ObjectTreeView` | section | Renders the `system_objects_*` tree for dev mode. Lazy-loads children on expand. Selecting a node loads ObjectEditor in ContentPanel. |
| `ContentPanel` | section | Main content area. Hosts CMS-rendered pages (standard mode) or ObjectEditor (dev mode). |
| `ObjectEditor` | section | Object detail editor rendered inside ContentPanel in dev mode. Loads `readObjectDetail` for the selected node and renders typed controls for each field. |
| `CollapsibleSection` | section | Expandable/collapsible container. Used by ObjectEditor for grouped fields. |
| `NavigationItem` | control | A single navigable route item. Shows icon + label (or icon-only when collapsed). Highlights active route. |
| `ObjectTreeNode` | control | A single node in the object tree. Icon (by object type) + name. Expand/collapse. Click to select. |
| `LoginControl` | control | Authentication widget. Login button when unauthenticated, user info when authenticated. |
| `UserProfileControl` | control | User info display with logout action. |
| `DevModeToggle` | control | Toggle switch that swaps mode between standard and dev. Only rendered for `ROLE_SERVICE_ADMIN`. |
| `HamburgerToggle` | control | Sidebar drawer expand/collapse button. |
| `StringControl` | control | Single-line text input/display. Used by ObjectEditor. |
| `BoolToggle` | control | Toggle switch / checkbox. Used by ObjectEditor and DevModeToggle. |
| `IntControl` | control | Integer input. Used by ObjectEditor. |
| `ReadOnlyDisplay` | control | Generic read-only value display for any type. Fallback for non-editable fields. |
| `ButtonLinkControl` | control | Clickable button-style link to a route or URL. Used for homepage navigation links. |

---

## 5. Dev Mode Interaction Flow

```
1. User clicks DevModeToggle in SidebarFooter
2. SidebarContent switches from NavigationTreeView to ObjectTreeView
3. ObjectTreeView calls readObjectTree(parent_guid: null)
4. Server returns top-level categories:
   - Types (11 children)
   - Database Tables (12 children)
   - Components (0 children — not yet populated)
   - Roles (11 children)
   - Entitlements (4 children)
5. User clicks "Database Tables" → expand
6. ObjectTreeView calls readObjectTree(parent_guid: tables_category_guid)
7. Server returns registered tables:
   - system_objects_types
   - system_objects_database_tables
   - system_objects_database_columns
   - system_users
   - service_auth_providers
   - system_user_auth
   - system_auth_roles
   - system_user_roles
   - system_auth_entitlements
   - system_user_entitlements
   - ... (legacy tables as migrated)
8. User clicks "system_users" → selected
9. ContentPanel loads ObjectEditor
10. ObjectEditor calls readObjectDetail(key_guid: system_users_guid, object_type: "table")
11. Server returns fields:
    - pub_name: "system_users" (STRING, editable: false — deterministic GUID source)
    - pub_schema: "dbo" (STRING, editable: true)
12. ObjectEditor also loads child grid: columns for this table
    - Calls readObjectTree(parent_guid: system_users_guid) for columns
    - Renders EditableGrid with column definitions
13. User edits a column's pub_max_length value → tab out
14. DecimalControl dispatches updateObjectField(key_guid, "table", "pub_max_length", 512)
15. Server validates and updates
```

---

## 6. Relationship to Current Code

### What Gets Replaced

| Current | Replaced By |
|---|---|
| `App.tsx` (React Router + layout) | `Workbench` component (CMS-driven root) |
| `NavBar.tsx` (flat route list) | `NavigationSidebar` with `NavigationTreeView` |
| `fetchNavbarRoutes` RPC call | `readNavigationRoutes` (hierarchical, role-pruned) |
| `<Outlet />` (React Router content) | `ContentPanel` with `CmsRenderer` |
| `frontend_pages` table (route → component map) | CMS route resolution (`resolveRoute`) |
| `frontend_links` table (nav link definitions) | Subsumed into the navigation route tree |

### What Gets Retained

| Current | Status |
|---|---|
| `DynamicIcon` component | Retained — NavigationItem uses it for icon rendering |
| `Login` component | Retained as `LoginControl` — may need minor refactor for new container |
| `UserContext` | Retained — workbench consumes it for auth state and dev mode eligibility |
| MUI theme and `LAYOUT` constants | Retained — workbench uses the same theme |
| React Router | Retained for URL management — workbench delegates route changes to the CMS resolver |

---

## 7. Object Tree Top-Level Structure

The object tree in dev mode presents the `system_objects_*` data as a navigable hierarchy. The top-level categories are virtual grouping nodes (not stored in the database — constructed by the server from the object tables):

```
Object Tree
├── 📐 Types (11)
│   ├── INT32
│   ├── INT64
│   ├── INT64_IDENTITY
│   ├── UUID
│   ├── BOOL
│   ├── DATETIME_TZ
│   ├── STRING
│   ├── TEXT
│   ├── INT8
│   ├── DATE
│   └── DECIMAL_19_5
├── 🗄️ Database (12 tables)
│   ├── system_objects_types
│   │   ├── Columns (13)
│   │   ├── Indexes (1)
│   │   └── Constraints (0)
│   ├── system_objects_database_tables
│   │   ├── Columns (5)
│   │   ├── Indexes (1)
│   │   └── Constraints (0)
│   ├── system_users
│   │   ├── Columns (5)
│   │   ├── Indexes (0)
│   │   └── Constraints (0)
│   ├── service_auth_providers
│   │   └── ...
│   └── ... (remaining tables)
├── 🔐 Security
│   ├── Roles (11)
│   │   ├── ROLE_REGISTERED
│   │   ├── ROLE_STORAGE
│   │   ├── ROLE_SUPPORT
│   │   ├── ...
│   │   └── ROLE_SERVICE_ADMIN
│   └── Entitlements (4)
│       ├── ENABLE_OPENAI_API
│       ├── ENABLE_LUMAAI_API
│       ├── ENABLE_DISCORD_BOT
│       └── ENABLE_MCP_ACCESS
├── 🧩 Components (0 — populated as CMS engine is built)
│   └── [component registrations will appear here]
├── 📄 Pages (0 — populated as page trees are defined)
│   └── [page tree roots will appear here]
└── 🔗 Routes (0 — populated as route bindings are created)
    └── [route → page mappings will appear here]
```

The Components, Pages, and Routes categories are empty initially. They populate as the CMS engine component registrations, page tree definitions, and route bindings are seeded.

---

## 8. Notes

- The `Workbench` is the only component that is *not* rendered by the CMS engine — it *is* the CMS engine's host. It is a static React component that bootstraps the entire system. Everything inside the ContentPanel is CMS-driven; the Workbench itself is code.

- **Two modes, one shell.** The Workbench always wraps both sidebar and content panel. In standard mode: NavigationTreeView in the sidebar, CMS-rendered pages in the content panel. In dev mode: ObjectTreeView in the sidebar, ObjectEditor in the content panel. The mode toggle swaps what fills both panels simultaneously.

- Dev mode is a **client-side state toggle**, not a route change. The URL does not change when entering dev mode. This keeps the URL bar clean and avoids polluting the route namespace with dev tooling.

- The object tree is the **self-hosting endpoint** of the CMS engine. Once the object tree editor can create component registrations, define component trees, and bind routes — the system can build its own pages.

- The `ObjectEditor` is a **section component** inside the ContentPanel, not a separate page. It renders any object type as a form based on the fields returned by `readObjectDetail`. Different object types will have different editors in the future (a table editor might show a column grid, a component tree editor might show a visual tree builder), but the initial implementation is a uniform field-based form.

- **No legacy fallback.** Everything is built greenfield through the CMS engine. There is no transitional coexistence with static `.tsx` page files. Routes are only registered once their component trees are fully defined.