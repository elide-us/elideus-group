## Vendors
 
**Route:** `/finance/approver/vendors`
 
*Manage the vendor registry — external parties that provide services, infrastructure, or goods to the organization. This is the business-level address book for all entities the organization transacts with.*
 
### Functional Activity
 
Vendors are the counterparties in financial transactions. Every billing import line item is associated with a vendor, every account mapping targets vendor-specific service patterns, and the service management page tracks vendor-related obligations (domain renewals, subscriptions, API keys).
 
This page is more than a name list — it's the registry of business relationships. Each vendor record captures who they are, what they provide, how the organization interacts with them, and whether they're currently active.
 
**When to use this page:**
- **Onboarding a new vendor:** When the organization begins using a new cloud provider, SaaS tool, or service, create a vendor record here. This makes the vendor available for account mappings (so billing imports can classify their costs) and service management (so renewals and expirations can be tracked).
- **Vendor details management:** Maintain display names, descriptions, and notes about each vendor — what they provide, how they're paid, contract terms, account identifiers.
- **Deactivation:** When a vendor relationship ends, deactivate rather than delete. Historical transactions referencing the vendor are preserved.
 
**Typical workflow:**
1. New cloud service or subscription starts → create a vendor record
2. Set up account mappings on the Admin's Account Mappings page to classify the vendor's billing data
3. Create service management entries for the vendor's renewals and expirations
4. Maintain vendor details as the relationship evolves
 
### Page Layout
 
Create button opens a collapsible inline form. Table displays all vendors with name, display name, description, status, and edit/delete actions.
 
### Functions
 
#### `readVendors`
 
- **Request:** none
- **Response:** `ReadVendorList1` — `{ elements: ReadVendorElement1[] }`
- `ReadVendorElement1` — `{ guid: string, name: string, display: string | null, description: string | null, status: int }`
 
#### `createVendor`
 
- **Request:** `CreateVendorParams1` — `{ name: string, display: string | null, description: string | null }`
- **Response:** `CreateVendorResult1` — `{ guid: string, name: string }`
 
*GUID is generated server-side (non-deterministic). Created with status active by default.*
 
#### `updateVendor`
 
- **Request:** `UpdateVendorParams1` — `{ guid: string, display: string | null, description: string | null, status: int }`
- **Response:** `UpdateVendorResult1` — `{ guid: string, name: string }`
 
*Name is immutable after creation — it serves as the human-readable identifier. Display name, description, and status are editable.*
 
#### `deleteVendor`
 
- **Request:** `DeleteVendorParams1` — `{ guid: string }`
- **Response:** `DeleteVendorResult1` — `{ guid: string }`
 
### Notes
 
- `readVendors` is a shared lookup consumed by the Admin's Account Mappings page (vendor filter and mapping form dropdown) and the Service Management page (vendor reference for tracked obligations).
- Vendor records are referenced by staging line items and account mappings via GUID FK — vendors with transaction history cannot be deleted, only deactivated.
 
### Description
 
Vendor registry management. The business-level address book for all external parties the organization transacts with. Collapsible inline form for create/edit with name, display name, description, and active toggle. Table with edit and delete controls. Vendors are referenced by account mappings, staging imports, and service management. Requires `ROLE_FINANCE_APPR`.
 