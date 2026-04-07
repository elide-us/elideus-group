## Financial Dimensions
 
**Route:** `/finance/admin/dimensions`
 
*Define name-value tag pairs that can be attached to journal lines for multi-dimensional reporting and analysis beyond the account structure.*
 
### Functional Activity
 
Financial dimensions add classification depth to journal entries. While the chart of accounts defines *what* was spent or earned, dimensions define *how* it should be sliced for reporting — by department, project, cost center, or any other analytical axis the organization needs.
 
Each dimension is a name-value pair. The name defines the axis (e.g., "Department", "Project", "CostCenter") and the value defines the specific tag within that axis (e.g., Department=Engineering, Department=Operations). Multiple dimensions with the same name create the set of available values for that axis.
 
**When to use this page:**
- **Initial setup:** Create the dimension axes and their values before accountants begin creating journals. Common starting dimensions: Department, Project, CostCenter, Vendor (as an analytical tag separate from the vendor registry).
- **Adding new values:** When a new department, project, or cost center is created in the organization, add a corresponding dimension value here so accountants can tag journal lines to it.
- **Deactivation:** Set status to inactive to prevent a dimension value from being used in new journal lines. Historical journal lines tagged with that dimension retain their association.
- **Billing import defaults:** Dimensions are referenced by the pipeline config (`default_dimension_recids`) to auto-tag imported billing journal lines. Ensure the referenced dimension recids are active.
 
**Typical workflow:**
1. Decide on the dimension axes the organization needs (Department, Project, etc.)
2. Create dimension entries for each axis-value combination
3. Note the recids of dimensions that should be applied to billing imports by default
4. Configure `default_dimension_recids` in Pipeline Config using those recids
5. Accountants select from available dimensions when creating manual journal lines
 
**Example dimension set:**
- Department=Engineering (recid 4)
- Department=Operations (recid 5)
- Project=TheOracleRPC (recid 15)
- CostCenter=Cloud (recid 16)
 
### Page Layout
 
Inline form at top for create/edit with dimension name, value, description, and save button. Table below showing all dimensions with edit and delete buttons.
 
### Functions
 
#### `readDimensions`
 
- **Request:** none
- **Response:** `ReadDimensionList1` — `{ elements: ReadDimensionElement1[] }`
- `ReadDimensionElement1` — `{ recid: int | null, name: string, value: string, description: string | null, status: int }`
 
#### `upsertDimension`
 
- **Request:** `UpsertDimensionParams1` — `{ recid: int | null, name: string, value: string, description: string | null, status: int }`
- **Response:** `UpsertDimensionResult1` — `{ recid: int, name: string, value: string }`
 
*Updates if `recid` is provided, inserts if null.*
 
#### `deleteDimension`
 
- **Request:** `DeleteDimensionParams1` — `{ recid: int }`
- **Response:** `DeleteDimensionResult1` — `{ recid: int }`
 
### Notes
 
- Dimensions are consumed by the Accountant's journal creation form as a multi-select tag picker on each journal line.
- The `dimension_recids` field on journal lines is a list of dimension recids — multiple dimensions can be applied to a single line.
- Dimension names are free-text, not a lookup table — the admin defines the naming convention. Consistency is enforced by convention, not by schema.
 
### Description
 
Financial dimension management page. Inline form for create/edit with dimension name, value, description, and status. Table displays all dimensions grouped implicitly by name. Dimensions are name-value tags attached to journal lines for multi-dimensional reporting. Used by accountants in journal creation and by the billing import pipeline for default tagging. Requires `ROLE_FINANCE_ADMIN`.
 