# CMS Rendering Engine — Implementation Spec

**Scope:** Design spec for the proof-of-concept implementation. Covers: the new `client/` frontend, the server-side CMS workbench module, the RPC contract, and the WorkbenchRenderer component. The goal is to load `/` and dynamically render `Workbench > ContentPanel > StringControl` showing the version number — with no hardcoded routes or page references in the client.

---

## 1. The Proof of Success

Loading `localhost:8000/` renders:
- A `Workbench` shell (sidebar + content panel)
- Inside the ContentPanel, a `StringControl` displaying `"0.12.4.0"` with label `"Version"`

Neither `Workbench` nor `StringControl` are referenced in `App.tsx`, a route table, or any import chain that the app knows about at compile time. They are rendered because the server told the client to render them. The client's only knowledge is:
- What a component looks like in code (the registry map)
- How to interpret the server's response (the rendering engine)

---

## 2. RPC Contract

### Request

```
POST /rpc
{
  "urn": "urn:public:route:load_path:1",
  "payload": { "path": "/" },
  "version": 1,
  "timestamp": "2026-04-09T..."
}
```

This uses the existing `HTTPRequest → RPCRequest → server module` pipeline. The URN routes through the `public` domain, `route` subdomain, `load_path` operation.

### Response

```typescript
interface LoadPathResponse {
  pathData: PathNode;
  componentData: Record<string, unknown>;
}
```

**PathData** — the component tree structure. Defines what to draw and where.

```typescript
interface PathNode {
  guid: string;                    // tree node GUID from system_objects_component_tree
  component: string;               // component name from system_objects_components
  category: string;                // "page" | "section" | "control"
  label: string | null;            // display label
  fieldBinding: string | null;     // key into componentData for this leaf's value
  sequence: number;                // render order within parent
  children: PathNode[];            // recursive children (empty array for leaves)
}
```

**ComponentData** — a flat key-value bag. Leaf components look up their `fieldBinding` key here to get the value to display.

```typescript
// For the proof-of-concept:
{
  "version": "0.12.4.0"
}

// Future example with more fields:
{
  "version": "0.12.4.0",
  "total_users": 42,
  "display_name": "Aaron Stackpole",
  "is_active": true
}
```

### Why Two Objects

PathData defines structure — what components exist and how they're nested. ComponentData defines values — what data fills those components. The separation exists because:

1. **Security pruning operates on PathData.** The server omits nodes the user can't see. The tree itself is the access control surface. Components that aren't in the tree don't render, period.

2. **ComponentData only contains values for components that survived pruning.** No leaked data for hidden fields.

3. **The rendering engine is stateless.** It receives a complete, pre-resolved, pre-secured snapshot. No additional queries, no client-side filtering, no logic beyond layout.

### Proof-of-Concept Response for `/`

```json
{
  "pathData": {
    "guid": "EE3B1A30-83A2-5990-96FE-99F8154138E3",
    "component": "Workbench",
    "category": "page",
    "label": null,
    "fieldBinding": null,
    "sequence": 1,
    "children": [
      {
        "guid": "4D268AF7-18BB-5CD1-886C-7EFE643560D5",
        "component": "ContentPanel",
        "category": "section",
        "label": null,
        "fieldBinding": null,
        "sequence": 2,
        "children": [
          {
            "guid": "...",
            "component": "StringControl",
            "category": "control",
            "label": "Version",
            "fieldBinding": "version",
            "sequence": 1,
            "children": []
          }
        ]
      }
    ]
  },
  "componentData": {
    "version": "0.12.4.0"
  }
}
```

Note: For the proof-of-concept, we're deliberately omitting the NavigationSidebar subtree from the PathData response. The server can do this — it's just returning a subset of the Workbench tree. We add the sidebar components once their implementations exist.

---

## 3. Server Side

### Module: `server/modules/cms_workbench_module.py`

Internal trusted module. Its job: given a path and user context, resolve the component tree and assemble the data payload.

```python
class CmsWorkbenchModule(BaseModule):
    """Internal module — renders component trees for paths.
    
    Not called directly by RPC. Called by the public:route RPC handler
    which unpacks the request and passes path + user context.
    """
    
    async def load_path(self, path: str, user_context: dict | None) -> dict:
        """
        1. Query system_objects_routes WHERE pub_path = path
        2. Get ref_root_node_guid → the root tree node
        3. Recursive CTE query on system_objects_component_tree
           starting from root, joining system_objects_components
           for component name and category
        4. Build the PathNode tree from the flat CTE result
        5. Assemble componentData for leaf nodes with field bindings
        6. Return { pathData: ..., componentData: ... }
        """
```

### The Recursive Query

The core of the module is a single recursive CTE that walks the component tree:

```sql
WITH tree AS (
    -- Anchor: root node
    SELECT
        t.key_guid,
        t.ref_parent_guid,
        t.pub_sequence,
        t.pub_label,
        t.pub_field_binding,
        c.pub_name AS component_name,
        c.pub_category AS component_category,
        0 AS depth
    FROM system_objects_component_tree t
    JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
    WHERE t.key_guid = @root_node_guid

    UNION ALL

    -- Recursive: children
    SELECT
        child.key_guid,
        child.ref_parent_guid,
        child.pub_sequence,
        child.pub_label,
        child.pub_field_binding,
        cc.pub_name,
        cc.pub_category,
        parent.depth + 1
    FROM system_objects_component_tree child
    JOIN tree parent ON parent.key_guid = child.ref_parent_guid
    JOIN system_objects_components cc ON cc.key_guid = child.ref_component_guid
)
SELECT * FROM tree ORDER BY depth, pub_sequence;
```

The module receives flat rows and assembles them into a nested tree in Python. This is a standard parent-child-to-tree transformation.

### Data Assembly

For the proof-of-concept, the `componentData` assembly is simple:

```python
# For each leaf node with a field_binding, resolve its value
component_data = {}
for node in flat_nodes:
    if node.pub_field_binding:
        # Proof-of-concept: pull version from system_config
        if node.pub_field_binding == "version":
            value = await self.db.run(
                "SELECT element_value FROM system_config WHERE element_key = 'Version'"
            )
            component_data["version"] = value
```

**Future state: Query objects in the object tree.** The data assembly will evolve into a system where component data requirements drive dynamically constructed queries defined in the object tree. If a particular route needs `intWholeNumber`, `boolToggleValue`, `floatDigits`, a query object will be created in the tree that defines the specific query — with whatever joins are required — to fulfill that component's data contract. These query objects are stored in the tree (not generated at runtime), but the system that builds and saves them may construct them dynamically based on the component's data requirements. This is a hybrid approach: queries are determined and persisted in the tree, not exclusively generated on the fly, but the tooling that creates them understands the component contracts well enough to compose the right joins and projections automatically. This replaces the legacy QueryRegistry pattern with something that is both data-driven and deterministic.

### RPC Handler: `rpc/public/route/`

Standard RPC handler structure following the existing pattern:

```
rpc/
  public/
    route/
      __init__.py
      handler.py      — dispatches to the module
      models.py       — Pydantic models for request/response
      services.py     — service dispatcher
```

**Models:**

```python
class LoadPathParams(BaseModel):
    path: str

class PathNode(BaseModel):
    guid: str
    component: str
    category: str
    label: str | None
    fieldBinding: str | None  # camelCase for the TypeScript contract
    sequence: int
    children: list['PathNode']

class LoadPathResult(BaseModel):
    pathData: PathNode
    componentData: dict[str, Any]
```

---

## 4. Client Side

### File Structure: `client/`

New folder at repo root, parallel to `frontend/`. Same build tooling (Vite + React 18 + MUI), same theme, independent entry point.

```
client/
├── index.html
├── package.json              — same deps as frontend
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── index.tsx              — mounts <App />
    ├── App.tsx                — boots Workbench via WorkbenchRenderer
    ├── api/
    │   └── rpc.ts             — rpcCall function (POST /rpc)
    ├── engine/
    │   ├── WorkbenchRenderer.tsx — the recursive rendering engine (root must be Workbench)
    │   ├── types.ts           — PathNode, ComponentData types
    │   └── registry.ts        — component name → React component map
    ├── components/
    │   ├── Workbench.tsx      — root shell (sidebar + content panel layout)
    │   ├── ContentPanel.tsx   — renders children passed by WorkbenchRenderer
    │   └── StringControl.tsx  — displays a string value with label
    └── theme/
        ├── ElideusTheme.ts    — copied from frontend/src/shared/theme/
        ├── layoutConstants.ts
        └── index.ts
```

### `src/App.tsx` — The Entire App

```tsx
import { useEffect, useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box, CircularProgress } from '@mui/material';
import { ElideusTheme } from './theme';
import { WorkbenchRenderer } from './engine/WorkbenchRenderer';
import { loadPath } from './api/rpc';
import type { PathNode } from './engine/types';

function App(): JSX.Element {
  const [pathData, setPathData] = useState<PathNode | null>(null);
  const [componentData, setComponentData] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPath(window.location.pathname)
      .then((res) => {
        setPathData(res.pathData);
        setComponentData(res.componentData);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <Box sx={{ p: 4, color: 'error.main' }}>{error}</Box>;
  if (!pathData) return <Box sx={{ p: 4 }}><CircularProgress /></Box>;

  return (
    <ThemeProvider theme={ElideusTheme}>
      <CssBaseline />
      <WorkbenchRenderer pathData={pathData} componentData={componentData} />
    </ThemeProvider>
  );
}

export default App;
```

Key point: **No imports of Workbench, ContentPanel, or StringControl.** No routes. No page references. Just `WorkbenchRenderer` receiving server data.

### `src/engine/types.ts` — The Contract

```tsx
export interface PathNode {
  guid: string;
  component: string;
  category: string;
  label: string | null;
  fieldBinding: string | null;
  sequence: number;
  children: PathNode[];
}

export interface CmsComponentProps {
  node: PathNode;
  data: Record<string, unknown>;
  children?: React.ReactNode;
}
```

### `src/engine/registry.ts` — The Component Map

```tsx
import type { CmsComponentProps } from './types';
import type { ComponentType } from 'react';
import { Workbench } from '../components/Workbench';
import { ContentPanel } from '../components/ContentPanel';
import { StringControl } from '../components/StringControl';

export const COMPONENT_REGISTRY: Record<string, ComponentType<CmsComponentProps>> = {
  Workbench,
  ContentPanel,
  StringControl,
};
```

This is the only file that imports concrete components. Adding a new component means: (1) write the `.tsx` file, (2) add one line to this map. The rendering engine discovers it by name.

### `src/engine/WorkbenchRenderer.tsx` — The Rendering Engine

```tsx
import type { PathNode, CmsComponentProps } from './types';
import { COMPONENT_REGISTRY } from './registry';
import { Box, Typography } from '@mui/material';

interface WorkbenchRendererProps {
  pathData: PathNode;
  componentData: Record<string, unknown>;
}

/**
 * Recursive renderer for component nodes.
 * Internal — called by WorkbenchRenderer for each node in the tree.
 */
function RenderNode({ node, data }: { node: PathNode; data: Record<string, unknown> }): JSX.Element {
  const Component = COMPONENT_REGISTRY[node.component];

  if (!Component) {
    return (
      <Box sx={{ p: 1, border: '1px dashed #333', m: 0.5 }}>
        <Typography variant="body2" color="text.secondary">
          Unknown component: {node.component}
        </Typography>
      </Box>
    );
  }

  const sortedChildren = [...node.children].sort(
    (a, b) => a.sequence - b.sequence
  );

  const renderedChildren = sortedChildren.map((child) => (
    <RenderNode key={child.guid} node={child} data={data} />
  ));

  return (
    <Component node={node} data={data}>
      {renderedChildren}
    </Component>
  );
}

/**
 * WorkbenchRenderer — entry point for the rendering engine.
 * Validates that the root node is a Workbench component, then
 * recursively renders the tree. This is the only renderer the
 * app knows about.
 */
export function WorkbenchRenderer({ pathData, componentData }: WorkbenchRendererProps): JSX.Element {
  if (pathData.component !== 'Workbench') {
    return (
      <Box sx={{ p: 4, color: 'error.main' }}>
        <Typography variant="h2">Rendering Error</Typography>
        <Typography variant="body1">
          Expected root component "Workbench", received "{pathData.component}".
        </Typography>
      </Box>
    );
  }

  return <RenderNode node={pathData} data={componentData} />;
}
```

**This is the entire engine.** `WorkbenchRenderer` validates the root is Workbench, then delegates to `RenderNode` which does three things:
1. Looks up the component by name in the registry
2. Sorts and recursively renders children
3. Passes `node` (for label, fieldBinding, etc.) and `data` (the ComponentData bag) as props

No logic. No decisions about what to render. The server already decided. The engine just draws.

### `src/components/Workbench.tsx`

```tsx
import type { CmsComponentProps } from '../engine/types';
import { Box } from '@mui/material';

const LAYOUT = {
  NAV_WIDTH_COLLAPSED: 48,
  PAGE_PADDING_X: 18,
  PAGE_PADDING_Y: 14,
};

export function Workbench({ children }: CmsComponentProps): JSX.Element {
  return (
    <Box sx={{
      display: 'flex',
      minHeight: '100vh',
      bgcolor: '#000000',
      color: '#FFFFFF',
    }}>
      {children}
    </Box>
  );
}
```

Workbench renders its children — whatever the server said they are. It doesn't know about ContentPanel or StringControl. It just provides the flex container.

### `src/components/ContentPanel.tsx`

```tsx
import type { CmsComponentProps } from '../engine/types';
import { Box } from '@mui/material';

export function ContentPanel({ children }: CmsComponentProps): JSX.Element {
  return (
    <Box component="main" sx={{
      flex: 1,
      minWidth: 0,
      overflowY: 'auto',
      py: '14px',
      px: '18px',
    }}>
      {children}
    </Box>
  );
}
```

### `src/components/StringControl.tsx`

```tsx
import type { CmsComponentProps } from '../engine/types';
import { Box, Typography } from '@mui/material';

export function StringControl({ node, data }: CmsComponentProps): JSX.Element {
  const value = node.fieldBinding ? data[node.fieldBinding] : null;

  return (
    <Box sx={{ mb: 1 }}>
      {node.label && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {node.label}
        </Typography>
      )}
      <Typography variant="body1">
        {value != null ? String(value) : '—'}
      </Typography>
    </Box>
  );
}
```

The StringControl reads its value from `data[node.fieldBinding]`. It doesn't know where the value came from. It doesn't know it's displaying a version number. It just renders a string with an optional label.

### `src/api/rpc.ts`

```tsx
import axios from 'axios';
import type { PathNode } from '../engine/types';

interface LoadPathResponse {
  pathData: PathNode;
  componentData: Record<string, unknown>;
}

export async function loadPath(path: string): Promise<LoadPathResponse> {
  const request = {
    urn: 'urn:public:route:load_path:1',
    payload: { path },
    version: 1,
    timestamp: new Date().toISOString(),
  };

  const response = await axios.post('/rpc', request);
  return response.data.payload as LoadPathResponse;
}
```

---

## 5. What Needs to Be Built (Codex Task List)

### Server Side

1. **Create `rpc/public/route/`** — standard RPC subdomain structure (`__init__.py`, `handler.py`, `models.py`, `services.py`). Register `load_path` as operation in the dispatcher.

2. **Create `server/modules/cms_workbench_module.py`** — internal module. On startup, gets DB reference. Exposes `load_path(path, user_context)` method. Uses the recursive CTE to walk the component tree. Assembles PathData + ComponentData.

3. **Register the module** in the server lifespan startup sequence.

4. **Add a StringControl tree node** under ContentPanel in `system_objects_component_tree` for the proof-of-concept. This is a one-row INSERT with:
   - `ref_parent_guid` = ContentPanel node GUID
   - `ref_component_guid` = StringControl component GUID
   - `pub_label` = "Version"
   - `pub_field_binding` = "version"
   - `pub_sequence` = 1

5. **ComponentData assembly** for the proof-of-concept: when a leaf has `fieldBinding = "version"`, query `system_config WHERE element_key = 'Version'` and include the value.

### Client Side

6. **Create `client/` folder** with Vite + React 18 + MUI. Copy theme from frontend. Create `index.html`, `package.json`, `tsconfig.json`, `vite.config.ts`.

7. **Create `src/engine/`** — `types.ts`, `registry.ts`, `WorkbenchRenderer.tsx`.

8. **Create `src/components/`** — `Workbench.tsx`, `ContentPanel.tsx`, `StringControl.tsx`.

9. **Create `src/api/rpc.ts`** — the `loadPath` function.

10. **Create `src/App.tsx`** — boots by calling `loadPath(window.location.pathname)` and passing the result to `WorkbenchRenderer`.

11. **Create `src/index.tsx`** — mounts `<App />` into `#root`.

### Build Configuration

12. **Configure Vite** to build into `../static-client/` (or similar) to avoid conflicting with the existing `../static/` output from `frontend/`.

13. **Add a second `StaticFiles` mount** in `main.py` or adjust the `web_router` catch-all to serve from the new build output during development.

### Seed Data

14. **Migration `v0.12.5.0`** — insert the StringControl tree node under ContentPanel for the `/` route proof-of-concept.

---

## 6. Design Principles (Enforced in Implementation)

1. **The client is a rendering engine, not a logic engine.** It draws the data it's given. No decisions about what to show, no access control, no data filtering.

2. **App.tsx has no component imports beyond WorkbenchRenderer.** The component registry is the only file that knows what components exist. App.tsx knows how to call the server and pass the result to the engine.

3. **Components receive `CmsComponentProps` and render.** Containers render `children`. Leaves read `data[fieldBinding]`. That's the full API.

4. **The server resolves everything.** Path → route → tree → prune → data → response. One RPC call, one response, one render. The client makes exactly one call on page load.

5. **ComponentData is flat.** No nesting, no structure. Just `{ key: value }` pairs. The PathData tree defines structure; ComponentData defines values. They're separate concerns.

---

## 7. What This Proves

If this works, we've proven:
- **Dynamic rendering from server data** — components are selected and composed by the server, not by client-side routing
- **The component registry pattern** — adding a component is: write the TSX, add one line to the registry map, register in the database
- **The PathData/ComponentData split** — structure and data travel separately, enabling independent security pruning
- **The WorkbenchRenderer recursion** — the engine can handle arbitrary nesting depths without knowing the tree structure in advance
- **Zero hardcoded pages** — the entire UI is driven by database definitions

This is the foundation everything else builds on. Once this works, we add NavigationSidebar, dev mode, the object tree editor, and then start defining page component trees for every page spec.