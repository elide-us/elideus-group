# TheOracleRPC — Object Tree Architecture

## Why the Object Tree Exists

A typical web application scatters its definition across code, configuration, database
schemas, and deployment artifacts. A page exists because a TSX file defines it. A route
exists because a router maps it. An API exists because a service function handles it.
A data model exists because a Pydantic class declares it. Security exists because a
decorator checks a role. Each of these lives in a different file, in a different language,
with a different lifecycle. When you want to change something, you touch code in three
layers, rebuild, redeploy, and hope nothing drifted.

The object tree eliminates this scatter. Every definable thing in the system — what
components exist, how they compose into pages, what data those pages need, what
functions serve that data, what modules implement those functions, what security gates
protect them, what types their fields use — is a row in a relational table with FK
constraints connecting it to everything it depends on.

The result is a system where the code doesn't make decisions. The data makes decisions.
The code just reads the data and draws what it says.

---

## The Shape of the System

The object tree is not one table. It's a family of tables organized into four domains
of concern, each answering a different question about the application.

### Domain 1: What can we build with?

The **type system** and **component registry**. Types define the twelve scalar data
shapes the system understands (INT32, STRING, UUID, BOOL, etc.) with mappings to every
target language (MSSQL, Python, TypeScript, JSON). Components define the finite set of
React elements that exist in code — each one registered by name with a category
(page, section, control) and optionally a default type.

Types and components grow slowly and deliberately. Adding a new component means writing
a TSX file, registering it in the client engine, and inserting one row. Adding a new
type means defining its cross-language mappings. These are the atomic building blocks.

The **type-to-control mapping** bridges these two: for any given type, which component
renders it by default? STRING → StringControl. BOOL → BoolToggle. This is many-to-many
with a default flag, so a STRING field can be overridden to render as a DropdownSelect
in a specific context without changing the global default.

### Domain 2: What does the application look like?

The **component tree**, **pages**, **routes**, and **data bindings**. This is where
the building blocks from Domain 1 get composed into actual application surfaces.

A **page** is a named definition (e.g., "home") that owns a root node in the component
tree. The component tree is recursive — each node references a registered component,
has a parent (or NULL for root), a sequence number for ordering among siblings, and
optional metadata like labels and field bindings. The tree defines the structure of
what renders.

A **route** maps a URL path to a page, which maps to a root tree node. Route → Page →
Tree Root → recursive CTE walk = the full component hierarchy for that URL.

**Data bindings** answer "where does the data come from?" for each component. A binding
ties a tree node to a data source: a literal string, a system config key, a database
column, or a server module method. The binding's `pub_alias` becomes the key in the
`componentData` dictionary that the component reads at render time.

The Workbench shell is itself a component tree — always present, always the root.
But the shell has multiple slots that get filled from different sources. The
NavigationSidebar loads its content from the route tree (navigation items derived
from `system_objects_routes`). The ContentPanel loads its content from the page
definition resolved by the current route. In dev mode, the ObjectTreeView loads
from the full object tree, and the ObjectEditor loads detail for the selected node.

Each of these is a separate data concern stitched into the same shell. The server
assembles one or more content trees into the Workbench frame before returning it
to the client. The client always sees a single unified tree rooted at Workbench
and recursively renders — it doesn't know how many sources contributed to the tree
it received. Today the minimum is three: the shell itself, the navigation content,
and the page content. As the system grows, more slots may load from more sources,
but the pattern is the same: the server composes, the client draws.

### Domain 3: What does the server do?

The **module registry** and **module methods**. Every server module is registered with
its `app.state` attribute name and its Python class path. Every callable method on
every module is registered with its name and a reference back to its parent module.

This is the internal implementation map. It answers "if I need to call a function,
what module owns it, and where do I find that module at runtime?" The RPC dispatch
system uses this to route an incoming URN to the correct Python method without any
hardcoded import chains.

### Domain 4: How does the outside world talk to us?

The **RPC namespace** — domains, subdomains, functions, models, and model fields.
This is the external API surface.

An RPC **domain** (public, system, service) is a security boundary gated by a role.
A **subdomain** (config, cms, routes) is a feature grouping gated by an entitlement.
A **function** is a single callable operation with a version, linking to a module method
via FK. Functions can also have their own role and entitlement requirements.

**Models** define the data contracts — the Pydantic shapes that flow between client
and server. Each model has **fields** with types (FK to the type registry), nullability,
list flags, and optional nested model references. The entire typed API surface is
data, not code.

The link between Domain 3 and Domain 4 is the FK from `rpc_function.ref_method_guid`
to `module_method.key_guid`. External dispatch resolves to internal implementation
through one join. No import chains, no file path conventions, no AST crawling.

---

## How the Domains Connect

The FK relationships between these domains form a graph that expresses the complete
shape of the application:

```
Route → Page → Tree Root
                  ↓
            Component Tree Node → Component (from registry)
                  ↓
            Data Binding → Column → Table → Type
                         → Config Key
                         → Literal Value
                         → Module Method → Module

RPC Function → Module Method → Module
RPC Function → Subdomain → Domain
RPC Function → Request Model → Model Fields → Type
RPC Function → Response Model → Model Fields → Type

Component Tree Node → Required Role
Component Tree Node → Required Entitlement
Route → Required Role
Domain → Required Role
Subdomain → Required Entitlement
```

Every arrow is a FK constraint. Every node is a row. If you can express a question as
"what X uses Y?" or "what Y does X need?", you can answer it with a single query that
walks the FK graph. What tables does this page need? Follow: page → bindings →
columns → tables. What security does this function require? Follow: function →
subdomain → domain, check role + entitlement FKs at each level.

---

## The Self-Describing Property

The object tree contains tables that describe database tables. `system_objects_database_tables`
has a row for itself. `system_objects_database_columns` has rows for its own columns.
The type registry has a type for UNIQUEIDENTIFIER, and the column registry uses that
type to describe the `key_guid` column on every table — including itself.

This isn't cleverness for its own sake. It means the ContractQueryBuilderModule can
derive a query for ANY page by walking the same column → table → constraint chain,
regardless of whether the target data lives in application tables, system tables,
or the object tree tables themselves. The system introspects its own structure through
the same mechanism it uses for application data.

---

## Content Forge: The Builder Pair

Two modules that close the loop — the system builds itself.

**ComponentBuilderModule** is the composer. It provides CRUD operations on tree nodes
and data bindings. When a designer adds a LinkButton to a page and binds it to a
database column, the ComponentBuilder inserts the tree node and the data binding row.
On certain design events (binding added, binding removed, save), it dispatches to
the ContractQueryBuilderModule.

**ContractQueryBuilderModule** is the analyzer. Given a page, it reads all data bindings,
resolves column bindings through the FK chain to tables and types, and produces two
concrete outputs: the SQL query text that will execute at render time, and the data
model definition (name, fields, types) that describes the query's result shape.

The query isn't abstract. It's a real SQL string: `SELECT u.pub_display AS display_name,
c.element_value AS credits FROM account_users u JOIN users_credits c ON c.ref_user_guid
= u.key_guid WHERE u.key_guid = @user_guid`. The model isn't abstract either: it's
explicit field definitions with names, types, and nullability that get written to the
model registry.

On save, the ComponentBuilder commits the tree + bindings + derived query + derived
model as one atomic unit. The derived artifacts use deterministic GUIDs based on the
page slug and field aliases, so re-saving updates in place rather than creating
duplicates.

The bootstrapping paradox: the ComponentBuilder UI will itself be a page definition
in the component tree, built using the components it manages, editing the tables it
reads from. The first pages are defined by hand in SQL — once the builder is live,
all future pages are defined through the builder, which is itself defined in the same
system.

---

## Why This Works

**Correctness is structural.** You can't create a tree node referencing a nonexistent
component — the FK won't allow it. You can't bind a page to a column that doesn't
exist. You can't call a function through an RPC operation that doesn't map to a
registered module method. The constraints ARE the tests.

**Change is data.** Add a link to the homepage? INSERT a tree node and a data binding.
Change a label? UPDATE one row. Reorder buttons? UPDATE sequence values. No build,
no deploy, no PR. The server reads fresh on every request.

**Security is pervasive.** Every layer — route, page, component, domain, subdomain,
function — has nullable FK references to roles and entitlements. NULL means public.
Non-null means gated. The server prunes the component tree before sending it to the
client — restricted nodes simply don't appear in the response.

**Derivation is mechanical.** The ContractQueryBuilder doesn't use heuristics or
inference. It walks FK chains: binding → column → table → type → constraint. The query
writes itself from the graph. The model writes itself from the bindings. If the data
relationships are correct, the derived artifacts are correct.

**The client is a drawing surface.** It receives a tree, looks up each component in
a static registry, and renders recursively. It doesn't know where the tree came from,
what security was applied, or how the data was derived. It draws what it's told to draw.

---

## Deterministic Identity

Every canonical definition uses UUID5 derived from a natural key against a fixed
namespace (`DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67`). The seed formulas follow a
consistent pattern: `uuid5(NS, '{entity_type}:{natural_key}')`.

Same seed data run against any database instance produces identical GUIDs. No drift
between environments. FKs always resolve. Instance data (user records, transactions,
sessions) uses random GUIDs because those are inherently unique per-instance.

---

## Current State

The homepage renders at `/` with eight data-driven components — an image, six link
buttons, and a copyright label — all sourced from data binding rows. The Workbench
shell stitches the page tree under ContentPanel. The NavigationSidebar renders as a
placeholder awaiting its TSX implementation. MCP tools call the rpcdispatch module
directly for schema and catalog introspection.

The next milestones are implementing the ComponentBuilder and ContractQueryBuilder
modules, building the dev mode ObjectTreeView, and processing the first column-sourced
data binding — which will be the first mechanically-derived query from the
ContractQueryBuilder. After that, the system builds the system.