# Content Pages

*This spec covers two pages that work together: an admin management page and a public reader/editor page.*

---

## Content Pages Management

**Route:** `/service-content-pages`

*Replaces the former ServicePagesPage (`/service-pages`). Admin interface following the canonical summary + headers + detail pattern.*

### Summary View

Aggregate stats:
- Total page count
- Active / inactive count
- Pages by type (article, legal, etc.)
- Pages by category

### Page Headers

Paginated list of all content pages showing key metadata at a glance. Clicking a page drills into the detail view.

### Page Detail

Selected page's management panel:
- Slug (immutable after creation — deterministic GUID source)
- Title (editable)
- Page type (editable, FK lookup)
- Category (editable, FK lookup, nullable)
- Sequence (editable — controls display ordering)
- Active status (toggle)
- Pinned status (toggle)
- Role access mask (will change with role system revamp)
- Created by / modified by (read-only, display names resolved from user FK)
- Created / modified timestamps (read-only)
- Link to public view at `/pages/{slug}`

### Functions

#### `readContentPageSummary`

- **Request:** none
- **Response:** `ReadContentPageSummaryResult1` — `{ total_pages: int, active_count: int, inactive_count: int, type_counts: object, category_counts: object }`

#### `readContentPageHeaders`

- **Request:** `ReadContentPageHeadersParams1` — `{ limit: int, offset: int }`
- **Response:** `ReadContentPageHeaderList1` — `{ elements: ReadContentPageHeaderElement1[] }`
- `ReadContentPageHeaderElement1` — `{ recid: int, guid: string, slug: string, title: string, page_type: string, category: string | null, sequence: int, is_active: bool, is_pinned: bool, modified_on: string }`

#### `readContentPageDetail`

- **Request:** `ReadContentPageDetailParams1` — `{ recid: int }`
- **Response:** `ReadContentPageDetailResult1` — `{ recid: int, guid: string, slug: string, title: string, page_type: string, category: string | null, sequence: int, is_active: bool, is_pinned: bool, roles: int, created_by_name: string, modified_by_name: string, created_on: string, modified_on: string, current_version: int, version_count: int }`

#### `createContentPage`

- **Request:** `CreateContentPageParams1` — `{ slug: string, title: string, content: string, page_type: string, category: string | null, sequence: int }`
- **Response:** `CreateContentPageResult1` — `{ recid: int, guid: string, slug: string }`

#### `updateContentPage`

- **Request:** `UpdateContentPageParams1` — `{ recid: int, title: string | null, page_type: string | null, category: string | null, sequence: int | null, is_active: bool | null, is_pinned: bool | null }`
- **Response:** `UpdateContentPageResult1` — `{ recid: int }`

#### `deleteContentPage`

- **Request:** `DeleteContentPageParams1` — `{ recid: int }`
- **Response:** `DeleteContentPageResult1` — `{ recid: int }`

---

## Content Page Viewer

**Route:** `/pages/:slug`

*Public-facing page reader with inline editing for authorized users. Functionally identical to current ContentPage.*

### View Mode

- Page title and last-modified date
- Rendered markdown content
- Edit button (visible if user has `can_edit` permission based on role mask)

### Edit Mode

- `MarkdownEditor` component (split-pane)
- Edit summary text field (optional)
- Save / Cancel buttons
- Saving creates a new version (append-only)

### Version History Footer

Collapsible table at the bottom of view mode:
- Columns: Version # | Date | Summary | Actions
- Restore button per version (creates new version with restored content)

### Functions

#### `readPage` (public)

- **Request:** `ReadPageParams1` — `{ slug: string }`
- **Response:** `ReadPageResult1` — `{ slug: string, title: string, content: string | null, version: int, permissions: { can_edit: bool }, element_modified_on: string | null }`

#### `createPageVersion` (authenticated)

- **Request:** `CreatePageVersionParams1` — `{ slug: string, content: string, summary: string | null }`
- **Response:** `CreatePageVersionResult1` — `{ slug: string, version: int }`

#### `readPageVersions` (authenticated)

- **Request:** `ReadPageVersionsParams1` — `{ slug: string }`
- **Response:** `ReadPageVersionList1` — `{ elements: ReadPageVersionElement1[] }`
- `ReadPageVersionElement1` — `{ recid: int, version: int, summary: string | null, created_on: string }`

#### `readPageVersion` (authenticated)

- **Request:** `ReadPageVersionParams1` — `{ slug: string, version: int }`
- **Response:** `ReadPageVersionResult1` — `{ version: int, content: string, summary: string | null, created_on: string }`

---

## Tables

### `content_pages`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_guid` | UNIQUEIDENTIFIER | Unique, default `newid()` |
| `element_slug` | NVARCHAR(256) | URL slug, unique, immutable after creation |
| `element_title` | NVARCHAR(512) | Page title |
| `element_page_type` | NVARCHAR(64) | Page type (article, legal, etc.), default `'article'` |
| `element_category` | NVARCHAR(128) | Category grouping, nullable |
| `element_roles` | BIGINT | Role access bitmask (will change with role revamp), default `0` |
| `element_is_active` | BIT | Active flag, default `1` |
| `element_is_pinned` | BIT | Pinned flag, default `0` |
| `element_sequence` | INT | Display ordering, default `0` |
| `element_created_by` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `element_modified_by` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

### `content_page_versions`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `pages_recid` | BIGINT | FK → `content_pages.recid` |
| `element_version` | INT | Version number, auto-incremented per page, default `1` |
| `element_content` | NVARCHAR(MAX) | Markdown content |
| `element_summary` | NVARCHAR(512) | Edit summary, nullable |
| `element_created_by` | UNIQUEIDENTIFIER | FK → `account_users.element_guid` |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*Unique constraint on `(pages_recid, element_version)`.*

## Notes

- `element_page_type` and `element_category` are currently raw strings — these should eventually become FK lookups, but are not blocking for rebuild.
- `element_roles` bitmask will change with the role system revamp — the functional behavior (server-computed `can_edit`) remains.
- Versions are append-only. Restore creates a new version with the old content.
- The admin management page (summary-header-detail) handles metadata CRUD. The public viewer handles content read/edit.
- The `MarkdownEditor` component is shared with the wiki system.
- Home page links to `/pages/terms-of-service` and `/pages/privacy-policy` — these are content pages with `page_type = 'legal'`.

## Description

Two-page content management system. Admin management page at `/service-content-pages` follows the canonical summary + headers + detail pattern for page metadata CRUD (create, update status/type/category/sequence, delete). Public viewer at `/pages/:slug` renders markdown with inline editing for authorized users and append-only version history with restore.