# Gallery

**Route:** `/gallery`

*Public-facing gallery of user-published content. Any user with storage can mark files as public via the File Manager; those files appear here. Registered users can report content for moderation review. Reported items are removed from view immediately pending human disposition.*

## View

Tabbed content filter across media types:
- Image
- Video
- Audio
- Document
- Misc

Each tab shows a card grid of published files matching that media type. Cards display:
- Content preview (inline image, audio player, video player, or file icon)
- Filename
- Author display name (resolved from `account_users.element_display` via `users_guid` join)
- Report button (authenticated users only)

Content type classification:
- `image/*` → Image
- `video/*` → Video
- `audio/*` → Audio
- `application/*` or `text/*` → Document
- Everything else → Misc

## Functions

### `readGallery` (public)

- **Request:** none
- **Response:** `ReadGalleryResult1` — `{ elements: ReadGalleryElement1[] }`
- `ReadGalleryElement1` — `{ user_guid: string, display_name: string, path: string, name: string, url: string, content_type: string }`

*Returns all files where `element_public = 1`, `element_deleted = 0`, and `element_reported = 0`. Author display name resolved via `account_users` join.*

### `reportFile` (authenticated)

- **Request:** `ReportFileParams1` — `{ user_guid: string, name: string }`
- **Response:** `ReportFileResult1` — `{ user_guid: string, name: string }`

*Sets `element_reported = 1` on the cache row. The file is immediately excluded from gallery results. `name` is the full relative path (`path/filename` or just `filename`).*

## Notes

- Gallery is a read-only public view — content management (publish/unpublish) is done in the File Manager.
- `user_guid` is passed in the report request because the reporting user is reporting *another user's* file — the owner GUID comes from the gallery item, not the session.
- Reported files remain in the owner's File Manager but are hidden from public gallery results until moderation disposition is set.
- The gallery does not paginate in the current design — all public non-reported files are returned. Pagination may be added as content volume grows.

## Description

Public gallery displaying user-published files in a tabbed card layout filtered by media type. Each card shows a content preview, filename, and author display name. Authenticated users can report content, which immediately hides it from the gallery pending moderation review.

---

# Moderation Queue

**Route:** `/moderation-queue`

*Moderator-facing page for reviewing reported and auto-flagged content. Follows the canonical summary + headers + detail pattern. Requires `ROLE_MODERATOR_USER`.*

## Summary View

Aggregate moderation stats:
- Total items pending review
- Items by content type (image, video, audio, document, misc)
- Items reported by users vs. auto-flagged by automation
- Total items reviewed (all time)
- Items by disposition (removed, restored, warned)

## Headers

Paginated list of reported items showing:
- Thumbnail / content type icon
- Filename
- Owner display name
- Reporter display name (if user-reported) or "Auto-flagged" (if automated)
- Reported date
- Current status (pending, reviewed)

Clicking an item drills into the detail view.

## Detail

Selected item's moderation panel:
- Content preview (image render, audio/video player, or file link)
- File metadata: filename, path, content type, size, created date, owner display name, owner public profile link
- Report context: who reported it (or automation source), when, report reason (if provided — future field)
- Moderation actions:
  - **Restore** — clears reported flag, file returns to gallery
  - **Remove** — soft-deletes the file from gallery permanently (sets a moderation disposition, does not delete from blob storage)
  - **Warn User** — restores the file but flags the owner account for moderation attention (downstream moderation flow TBD)
- Disposition history (if the item has been reviewed before)

## Table: `moderation_queue` (new)

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_guid` | UNIQUEIDENTIFIER | Unique, default `newid()` |
| `users_guid` | UNIQUEIDENTIFIER | FK → `account_users.element_guid`, file owner |
| `element_path` | NVARCHAR(512) | File path in storage cache |
| `element_filename` | NVARCHAR(512) | Filename in storage cache |
| `reporter_guid` | UNIQUEIDENTIFIER | FK → `account_users.element_guid`, nullable (null = auto-flagged) |
| `element_source` | NVARCHAR(32) | Report source: `user`, `automation`, default `'user'` |
| `element_reason` | NVARCHAR(512) | Report reason, nullable (future — not currently collected) |
| `element_status` | NVARCHAR(32) | `pending`, `reviewed`, default `'pending'` |
| `element_disposition` | NVARCHAR(32) | `restored`, `removed`, `warned`, nullable (null while pending) |
| `moderator_guid` | UNIQUEIDENTIFIER | FK → `account_users.element_guid`, nullable (set on review) |
| `element_reviewed_on` | DATETIMEOFFSET(7) | Nullable, set on review |
| `element_created_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |
| `element_modified_on` | DATETIMEOFFSET(7) | Default `SYSUTCDATETIME()` |

*The `moderation_queue` table is the audit trail. The `users_storage_cache.element_reported` flag is the live gate — setting `element_reported = 1` hides the file immediately. The queue row tracks who reported it, why, and what the moderator decided.*

## Lookup Table: `moderation_dispositions`

| Column | Type | Notes |
|---|---|---|
| `recid` | BIGINT IDENTITY(1,1) | PK |
| `element_name` | NVARCHAR(32) | Disposition key (`restored`, `removed`, `warned`) |

*Seed values: `restored`, `removed`, `warned`.*

## Functions

### `readModerationSummary`

- **Request:** none
- **Response:** `ReadModerationSummaryResult1` — `{ pending_count: int, by_content_type: object, by_source: object, total_reviewed: int, by_disposition: object }`

### `readModerationHeaders`

- **Request:** `ReadModerationHeadersParams1` — `{ limit: int, offset: int, status: string | null }`
- **Response:** `ReadModerationHeaderList1` — `{ elements: ReadModerationHeaderElement1[] }`
- `ReadModerationHeaderElement1` — `{ recid: int, guid: string, owner_display_name: string, filename: string, content_type: string, source: string, reporter_display_name: string | null, status: string, created_on: string }`

### `readModerationDetail`

- **Request:** `ReadModerationDetailParams1` — `{ recid: int }`
- **Response:** `ReadModerationDetailResult1` — `{ recid: int, guid: string, owner_guid: string, owner_display_name: string, owner_public_id: string, path: string, filename: string, url: string, content_type: string, source: string, reason: string | null, reporter_display_name: string | null, status: string, disposition: string | null, moderator_display_name: string | null, reviewed_on: string | null, created_on: string }`

### `setModerationDisposition`

- **Request:** `SetModerationDispositionParams1` — `{ recid: int, disposition: string }`
- **Response:** `SetModerationDispositionResult1` — `{ recid: int, disposition: string }`

*Server-side effects by disposition:*
- `restored` → clears `element_reported` on the cache row, file returns to gallery
- `removed` → sets `element_public = 0` on the cache row (unpublishes), reported flag stays
- `warned` → clears `element_reported` (file returns to gallery), flags the owner account for moderation attention (mechanism TBD)

*The moderator's GUID is captured from auth context, not from the request payload.*

## Integration with Report Flow

When a user reports a file via `reportFile`:
1. `element_reported = 1` is set on `users_storage_cache` — file is immediately hidden from gallery
2. A new row is inserted into `moderation_queue` with `status = 'pending'`, `source = 'user'`, and the reporter's GUID

When automation flags content (future):
1. Same `element_reported = 1` flag
2. Queue row with `source = 'automation'`, `reporter_guid = NULL`

## Notes

- The report action is intentionally simple — no reason field is collected from the user in the current design. The `element_reason` column exists for future use.
- Moderation dispositions are final per review cycle. If a restored file is reported again, a new queue row is created.
- The moderator cannot edit file content or metadata — only set a disposition.
- `owner_public_id` in the detail response allows the moderator to view the owner's public profile for context.
- The `moderation_queue` table references the storage cache by `users_guid + path + filename` composite (not by a single FK), matching the cache table's natural key.
- GDPR: moderation queue rows are retained for audit purposes. The file content itself lives in blob storage and is not affected by moderation actions — only the `element_public` and `element_reported` flags on the cache row change.

## Description

Moderation queue page for reviewing reported and auto-flagged gallery content. Follows summary + headers + detail pattern. Summary shows pending counts and disposition breakdown. Headers list reported items with owner, reporter, and status. Detail view shows content preview, file metadata, report context, and moderation action buttons (restore, remove, warn). Dispositions update both the queue audit trail and the storage cache flags.