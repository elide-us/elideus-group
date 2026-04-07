# Schema Visualization

**Route:** `/service-schema`

*Interactive force-directed graph visualization of the database schema. Renders tables as nodes and foreign keys as edges on a full-viewport canvas. This page is functionally complete and this spec documents the exact behavior for rebuild fidelity.*

## Data

### Function

#### `readFullSchema`

- **Request:** none
- **Response:** `ReadFullSchemaResult1` — `{ tables: ReadSchemaTableElement1[], foreign_keys: ReadSchemaForeignKeyElement1[] }`
- `ReadSchemaTableElement1` — `{ recid: int, element_name: string }`
- `ReadSchemaForeignKeyElement1` — `{ tables_recid: int, referenced_tables_recid: int, element_column_name: string }`

*Single RPC call on mount. All rendering is client-side from this data.*

## Layout

Full-viewport page with three zones stacked vertically:

### Header Bar
- Page title: "Schema Visualization"
- Stats: `{tableCount} tables · {edgeCount} relationships`
- Color legend: one dot per domain prefix, auto-generated from table name prefixes, right-aligned, wraps

### Canvas
- `<canvas>` element filling all remaining vertical space
- Black background (`#000000`)
- Cursor: `grab` (default), `pointer` (over node)

### Info Panel (bottom)
- Fixed minimum height 44px, expands to max 220px when a node is active
- Transitions smoothly (`max-height 0.15s ease`)
- When no node is active: italic hint text — "Hover over a node to inspect. Click to pin. Scroll to zoom, drag to pan, drag nodes to reposition."
- When a node is active: three-column grid (Table info | Outgoing FK | Incoming FK)

## Graph Construction

### Domain Color Assignment
- Extract domain prefix from each table name (first segment before `_`)
- Sort unique domain prefixes alphabetically
- Assign colors from a 16-color palette in order, cycling if more than 16 domains
- Each color has three values: `fill` (node body), `stroke` (node border), `glow` (shadow rgba)

### 16-Color Palette
```
#4CAF50 / #81C784 / rgba(76,175,80,0.5)     — green
#BF8C2C / #D4A845 / rgba(191,140,44,0.5)     — amber
#1565C0 / #42A5F5 / rgba(21,101,192,0.4)     — blue
#00838F / #26C6DA / rgba(0,131,143,0.4)       — cyan
#5865F2 / #7983F5 / rgba(88,101,242,0.4)     — indigo
#6A1B9A / #AB47BC / rgba(106,27,154,0.4)     — purple
#546E7A / #90A4AE / rgba(84,110,122,0.3)     — blue-grey
#C62828 / #EF5350 / rgba(198,40,40,0.4)       — red
#2E7D32 / #66BB6A / rgba(46,125,50,0.4)       — dark green
#E65100 / #FF9800 / rgba(230,81,0,0.4)        — orange
#1B5E20 / #43A047 / rgba(27,94,32,0.35)      — forest
#4527A0 / #7E57C2 / rgba(69,39,160,0.4)      — deep purple
#00695C / #26A69A / rgba(0,105,92,0.4)        — teal
#AD1457 / #EC407A / rgba(173,20,87,0.4)       — pink
#37474F / #78909C / rgba(55,71,79,0.3)        — slate
#827717 / #C0CA33 / rgba(130,119,23,0.4)      — lime
```

### Node Properties
- **Radius:** `8 + (refs / maxRef) * 34` — scaled by incoming reference count relative to the most-referenced table
- **Initial position:** distributed in a circle (angle = index/total * 2π) with radius `220 + random * 120`, centered at (500, 400)
- **Self-references:** counted separately (FK where `from === to`), displayed in info panel but self-ref edges excluded from graph rendering
- **Outgoing/Incoming:** each node tracks its outgoing `{ target, col }[]` and incoming `{ source, col }[]` FK relationships

### Physics Simulation
Run 250 iterations before first render (not animated — computes offline then draws once):

- **Repulsion:** Every node pair, force = `9000 * alpha / dist²`, minimum distance = `r_a + r_b + 10`
- **Edge attraction:** Connected nodes, force = `(dist - ideal) * 0.004 * alpha`, ideal distance = `90 + r_a + r_b`
- **Center gravity:** Each node pulled toward (500, 400) at `0.008 * alpha`
- **Damping:** velocity multiplied by `0.82` per iteration
- **Alpha decay:** `alpha = 1 - iter / 250` (linear cooldown)

## Rendering

### Edges
- Default: white at 8% opacity (`rgba(255,255,255,0.08)`), 0.7px width
- Highlighted (connected to active node): green (`#4CAF50`), 2px width, green glow shadow (blur 8)
- Highlighted edges get directional arrowheads: 7px triangle at the target node's edge (offset by target radius)

### Nodes
- Circle filled with domain `fill` color, bordered with domain `stroke` color at 1.2px
- Active node: white border at 2.5px, domain glow shadow at blur 24
- Connected nodes: domain glow shadow at blur 12
- Dimmed nodes (when another node is active): fill at 13% opacity (`fill + "22"`), stroke at 20% opacity (`stroke + "33"`), no shadow
- Unrelated nodes with no active selection: domain glow at blur 6

### Labels
- Shown for: active node (always), connected nodes (when zoom > 0.5)
- Font: `500 {fontSize}px "Roboto", "Arial", sans-serif`, size = `max(10, 11 / zoom)`
- Position: centered above node, offset by `node.r + 6` pixels
- Text shadow: black offset (1, 1) behind domain-colored or white text
- Active node label: white. Connected node label: domain stroke color

## Interaction

### Hover
- Mouse over a node sets it as hovered, highlights it and all connected nodes/edges, dims everything else
- Info panel expands to show table details
- Cursor changes to `pointer`

### Click to Pin (NEW — not in current implementation)
- Clicking a node "pins" it — the info panel and highlighting stay active even when the mouse moves away
- Clicking the same pinned node unpins it (returns to hover behavior)
- Clicking a different node while one is pinned switches the pin to the new node
- A pinned node should show a subtle visual indicator (e.g. a small dot or ring) to distinguish from hover state

### Drag Node
- Mousedown on a node starts dragging — the node follows the cursor
- Dragging overrides hover behavior during the drag
- Mouseup ends the drag, node stays at new position
- Drag offset is preserved (grab point relative to node center)

### Pan Canvas
- Mousedown on empty space starts panning
- Canvas translates with mouse movement
- Mouseup ends panning

### Zoom
- Scroll wheel zooms in/out
- Zoom factor: `1.1` per scroll-up tick, `0.9` per scroll-down tick
- Range: `0.15` to `5.0`
- Zoom is anchored to the cursor position (focal-point zoom)

## Info Panel Detail

Three-column grid when a node is active:

### Column 1: Table
- Label: "TABLE" (uppercase, small, grey)
- Table name in monospace, domain stroke color, text glow
- Domain prefix (bold)
- Self-ref count if > 0
- Two stat boxes:
  - "Referenced by" count (green `#4CAF50`)
  - "References" count (amber `#BF8C2C`)

### Column 2: Outgoing FK
- Label: "OUTGOING FK" (uppercase, small, grey)
- Each FK: column name (monospace, grey) → target table name (bold, target domain color)
- "None (root table)" if empty

### Column 3: Incoming FK
- Label: "INCOMING FK" (uppercase, small, grey)
- Each FK: source table name (bold, source domain color) via column name (monospace, grey)
- "None (leaf table)" if empty
- Scrollable at 120px max height

## Technical Details

- Pure canvas rendering — no SVG or DOM nodes for the graph
- Device pixel ratio handling: canvas dimensions scaled by `window.devicePixelRatio` for sharp rendering on HiDPI displays
- `ResizeObserver` on canvas for responsive redraw
- Graph data stored in a `useRef` (not state) to avoid re-render on node drag
- Pan/zoom stored in state to trigger redraws
- Hit testing: find closest node within `node.r + 5` pixels of cursor in world coordinates

## Notes

- This page calls `service:reflection` RPC which is shared with the RPC Model Viewer and MCP server — do not delete that subdomain.
- The page is entirely client-side after the initial data load — no further RPC calls.
- The physics simulation is deterministic given the same input data, but initial positions include a random spread component so layouts vary between loads.
- Loading state shows centered "Loading schema data..." text.

## Description

Full-viewport interactive force-directed graph visualization of the database schema. Tables rendered as nodes sized by reference count, colored by domain prefix. Foreign keys rendered as edges with directional arrowheads on highlight. Click a node to pin its info panel (click again to unpin). Drag nodes to reposition, pan the canvas, scroll to zoom. Bottom info panel shows table name, domain, reference counts, and outgoing/incoming FK details. Color legend in header bar.
