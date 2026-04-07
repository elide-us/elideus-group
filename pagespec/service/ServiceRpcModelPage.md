# RPC Model Viewer

**Route:** `/service-rpc-models`

*Replaces the former ServiceRpcDispatchPage (`/service-rpc-dispatch`) and ServiceRpcDispatchTreePage (`/service-rpc-dispatch-tree`). Consolidates into a single page with summary and tree view.*

## Purpose

Read-only introspection of the live RPC topology. Provides a summary of the platform's API surface and a hierarchical tree view for navigating the full structure from domain down to individual model fields.

This interface is also consumed by the MCP server (`TheOracleMCP`) to provide LLM agents with platform intelligence — agents use the same underlying data to discover available operations, understand request/response contracts, and analyze the API surface for planning and code generation.

## Summary View

Aggregate counts of the RPC metadata:
- Domain count
- Subdomain count
- Function count
- Model count
- Model field count

## Tree View

Hierarchical expandable tree: Domain → Subdomain → Function → Request/Response Models → Fields.

- **Domain nodes** show: name, required role, auth/public/discord flags
- **Subdomain nodes** show: name, function count
- **Function nodes** show: name, version, module binding, status
- **Model nodes** show: request (inbound) or response (outbound) label, model name
- **Field nodes** show: field name, EDT type, nullability, list/dict flags, default value, referenced model name (if FK)

Expand all / collapse all / refresh controls.

## Functions

### `readRpcSummary`

- **Request:** none
- **Response:** `ReadRpcSummaryResult1` — `{ domain_count: int, subdomain_count: int, function_count: int, model_count: int, field_count: int }`

### `readRpcTree`

- **Request:** none
- **Response:** `ReadRpcTreeResult1` — `{ domains: ReadRpcDomainElement1[] }`
- `ReadRpcDomainElement1` — `{ name: string, required_role: string | null, is_auth_exempt: bool, is_public: bool, is_discord: bool, status: int, subdomains: ReadRpcSubdomainElement1[] }`
- `ReadRpcSubdomainElement1` — `{ name: string, entitlement_mask: int, status: int, functions: ReadRpcFunctionElement1[] }`
- `ReadRpcFunctionElement1` — `{ name: string, version: string, module_attr: string, method_name: string, status: int, request_model: ReadRpcModelElement1 | null, response_model: ReadRpcModelElement1 | null }`
- `ReadRpcModelElement1` — `{ name: string, fields: ReadRpcFieldElement1[] }`
- `ReadRpcFieldElement1` — `{ name: string, edt_name: string | null, is_nullable: bool, is_list: bool, is_dict: bool, ref_model_name: string | null, default_value: string | null, sort_order: int }`

## Notes

- Data comes from the `reflection_rpc_*` tables and `reflection_db_edt_mappings` lookup.
- This is a read-only diagnostic and development tool — no create/update/delete operations.
- EDT names and referenced model names are resolved server-side and returned as denormalized display fields.
- The tree response is a single nested payload — the server assembles the full hierarchy rather than requiring multiple round trips.
- The MCP server exposes the same reflection data through its `oracle_list_rpc_*` tools. The frontend page and MCP tools share the same underlying data source but may differ in response shape — the page gets a pre-assembled tree, MCP tools return flat lists for flexible agent consumption.

## Description

Read-only RPC topology viewer. Summary shows aggregate counts of domains, subdomains, functions, models, and fields. Tree view provides hierarchical navigation of the full API surface from domain to field level. Used for development diagnostics, platform introspection, and as the visual counterpart to the MCP agent intelligence tools.
