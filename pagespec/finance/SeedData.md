# Finance & System Seed Data

## Chart of Accounts (`finance_accounts`)

Account types: 0 = Asset, 1 = Liability, 2 = Equity, 3 = Revenue, 4 = Expense

### Header Accounts (non-posting)

| Number | Name | Type | GUID |
|--------|------|------|------|
| 1000 | Assets | Asset | 31A28AA0-BA53-4370-BCCF-632E8238735E |
| 2000 | Liabilities | Liability | 7C1FA400-6DF0-4F86-9282-184DA2DDB0E4 |
| 3000 | Equity | Equity | D20171F3-DB09-4E41-8ABA-9E1F12DA714B |
| 4000 | Revenue | Revenue | 911CE6FF-ED49-4841-B42E-89973FC8D7C9 |
| 5000 | Expenses | Expense | 7C3B3F89-E616-45E1-B1A3-E392F3B5ABDF |
| 5600 | Number Sequences | Expense | CE527F59-2D44-44F2-8820-C1A478035AB6 |

### Posting Accounts

| Number | Name | Type | Parent | GUID |
|--------|------|------|--------|------|
| 1100 | Cash | Asset | 1000 | E1410D6A-BB5E-46BA-ABBE-74AD52C20F81 |
| 1200 | Accounts Receivable | Asset | 1000 | 3D40F29A-90CF-4F70-975C-1973BED7C64F |
| 1300 | Payment Processor Clearing | Asset | 1000 | 65F8C8EC-DB0B-4D58-89E5-4FA9DB988C5E |
| 2100 | Deferred Revenue | Liability | 2000 | 083A1893-D64C-43EB-9700-58C844636F24 |
| 2200 | Accounts Payable | Liability | 2000 | B7FE2F7F-5ECC-4947-970C-A37028EC5327 |
| 2300 | Accrued Expenses | Liability | 2000 | 17E0D78C-B184-41BD-8AA3-07C4086FF759 |
| 3100 | Owner's Equity | Equity | 3000 | 872DA7A6-6A6B-4840-A7A2-70550A090082 |
| 3200 | Retained Earnings | Equity | 3000 | 076A2D02-B1E8-4B6E-A5F2-FB89A512A66A |
| 4010 | Recognized Revenue | Revenue | 4000 | A8804F9F-AD71-4540-A19C-ED125FE4C2B4 |
| 4020 | Breakage Revenue | Revenue | 4000 | 60B547D9-89DE-4DD7-B1E2-059D8E66E055 |
| 4030 | Contra-Revenue / Refunds | Revenue | 4000 | 2EB7BAC0-E7A7-474A-B6D0-CAF24F80C4D0 |
| 4100 | SaaS Subscriptions | Revenue | 4000 | 144E63E6-F2CC-46FC-A764-0C98F2710814 |
| 4200 | Credit Purchases | Revenue | 4000 | DAAD4CD3-666A-4D30-9E86-DFD83F4DD157 |
| 4300 | Contract Revenue | Revenue | 4000 | 36A092CE-4DEE-4A04-BF5A-2C01C70FA66F |
| 5010 | Merchant Fee Expense | Expense | 5000 | 20F764BD-1628-4F25-A3C2-BA1419E1DDBE |
| 5100 | Azure Infrastructure | Expense | 5000 | FB72A666-E9C3-47B5-A3D8-7A93D2132FC5 |
| 5110 | Azure App Service | Expense | 5000 | 41C8402B-B534-4A38-8001-47413D2973A4 |
| 5120 | Azure SQL Database | Expense | 5000 | C9BF5326-60A7-45A0-AF1F-A0E0BED6CD71 |
| 5130 | Azure Storage | Expense | 5000 | 8CA13447-27EB-4087-8465-8B79716B2352 |
| 5140 | Azure Container Registry | Expense | 5000 | D3E406AF-03D0-4CBE-BC05-CE737E20F6F3 |
| 5150 | Azure Networking | Expense | 5000 | 79330229-D980-4C92-A5BD-CA96ED9818A5 |
| 5200 | AI Services | Expense | 5000 | 1E5CDBBA-E980-4A84-B7D5-BF6F7972B0C2 |
| 5210 | OpenAI API | Expense | 5000 | C4DDC0D5-01F3-4264-84AB-BF0E7A564717 |
| 5220 | Luma Labs API | Expense | 5000 | 8C5CBFB6-7FC7-4DDB-994E-F3917C461939 |
| 5300 | Development Tools | Expense | 5000 | 70457CC2-25DD-4041-BEA0-528B94F21C99 |
| 5310 | GitHub | Expense | 5000 | 8FEE8BBC-F3DB-4B38-A9B0-B1C0F096D851 |
| 5320 | Domain Registration | Expense | 5000 | D443E02B-21E4-4621-ADEB-7D4F1D7D8606 |
| 5400 | General & Administrative | Expense | 5000 | 551C71AB-E53F-4F42-B089-40C3E11A6046 |
| 6100 | Owner Usage | Expense | 5000 | FD6C5463-F8A3-432A-84B6-3C4FB09AFB0B |
| 6200 | Marketing Expense | Expense | 5000 | 61F09DD7-B832-4315-820D-48B03DEEE4FB |

### Non-Posting Sub-Headers (under Expenses)

| Number | Name | Parent | GUID |
|--------|------|--------|------|
| 5610 | Journal Sequences | 5600 | F81CE288-CE21-4300-BAD7-8C7672D38A21 |
| 5620 | Lot Sequences | 5600 | 8633E288-F305-4FD3-93CF-4801B43C1878 |
| 5630 | Transaction Sequences | 5600 | 477C77D6-A485-43E0-B0F7-B7BB7E90BEF5 |

---

## Financial Dimensions (`finance_dimensions`)

| Name | Value | Description |
|------|-------|-------------|
| Department | Engineering | Software development and infrastructure |
| Department | Operations | Business operations and administration |
| CostCenter | CC-INFRA | Azure infrastructure costs |
| CostCenter | CC-AI | AI service API costs |
| CostCenter | CC-DEV | Development tooling costs |
| ServiceType | IMG | Image generation service |
| ServiceType | VID | Video generation service |
| ServiceType | TTS | Text-to-speech service |
| ServiceType | CHAT | Chat/conversation service |
| Vendor | Azure | Microsoft Azure |
| LotSource | purchase | Customer credit purchase |
| LotSource | grant_owner | Owner/admin credit grant |
| LotSource | grant_promo | Promotional credit grant |
| LotSource | grant_signup | Signup bonus credits |

---

## Frontend Links (`frontend_links`)

| recid | Seq | Title | URL |
|-------|-----|-------|-----|
| 1 | 10 | Discord | https://discord.gg/xXUZFTuzSw |
| 2 | 20 | GitHub | https://github.com/elide-us |
| 3 | 30 | TikTok | https://www.tiktok.com/@elide.us |
| 4 | 40 | BlueSky | https://bsky.app/profile/elideusgroup.com |
| 5 | 50 | Suno | https://suno.com/@elideus |
| 6 | 60 | Patreon | https://patreon.com/Elideus |

---

## Storage Types (`storage_types`)

| recid | MIME Type | Display Type |
|-------|-----------|-------------|
| 1 | application/octet-stream | Binary |
| 2 | text/plain | Text |
| 3 | text/markdown | Text |
| 4 | application/json | Data |
| 5 | application/pdf | Document |
| 6 | image/png | Image |
| 7 | image/jpeg | Image |
| 8 | image/gif | Image |
| 9 | image/webp | Image |
| 10 | video/mp4 | Video |
| 11 | video/webm | Video |
| 12 | audio/mpeg | Audio |
| 13 | audio/wav | Audio |
| 14 | audio/ogg | Audio |
| 15 | audio/flac | Audio |
| 16 | path/folder | Folder |

---

## System Roles (`system_roles`)

| Name | Display | RPC Domain |
|------|---------|------------|
| ROLE_REGISTERED | Registered User | users |
| ROLE_STORAGE | Storage Enabled | storage |
| ROLE_SUPPORT | Support | support |
| ROLE_MODERATOR | Moderator | moderation |
| ROLE_FINANCE_ACCT | Accountant | — |
| ROLE_FINANCE_APPR | Accounting Manager | — |
| ROLE_DISCORD_ADMIN | Discord Admin | discord |
| ROLE_ACCOUNT_ADMIN | Account Admin | account |
| ROLE_FINANCE_ADMIN | Finance Admin | finance |
| ROLE_SYSTEM_ADMIN | System Admin | system |
| ROLE_SERVICE_ADMIN | Service Admin | service |

---

## System Entitlements (`system_entitlements`)

| Name | Display | RPC Domain |
|------|---------|------------|
| ROLE_OPENAI_API | OpenAI Generation | — |
| ROLE_LUMAAI_API | LumaAI Generation | — |
| ROLE_DISCORD_BOT | Discord Bot | — |
| ROLE_MCP_ACCESS | MCP Agent Access | — |

---

"""Finance status code constants.

These values must stay in sync with the finance_status_codes table.
Management of status codes is via Finance Admin UI → status codes table.
"""

# Import statuses (finance_staging_imports.element_status)
IMPORT_PENDING = 0
IMPORT_APPROVED = 1
IMPORT_FAILED = 2
IMPORT_PROMOTED = 3
IMPORT_PENDING_APPROVAL = 4
IMPORT_REJECTED = 5

# Journal statuses (finance_journals.element_status)
JOURNAL_DRAFT = 0
JOURNAL_PENDING_APPROVAL = 1
JOURNAL_POSTED = 2
JOURNAL_REVERSED = 3

# Period statuses (finance_periods.element_status)
PERIOD_OPEN = 1
PERIOD_CLOSED = 2
PERIOD_LOCKED = 3

# Period close types (finance_periods.element_close_type)
CLOSE_TYPE_NONE = 0
CLOSE_TYPE_QUARTERLY = 1
CLOSE_TYPE_ANNUAL = 2

# Generic element status
ELEMENT_INACTIVE = 0
ELEMENT_ACTIVE = 1

# Credit lot statuses
CREDIT_LOT_ACTIVE = 1
CREDIT_LOT_EXHAUSTED = 2
CREDIT_LOT_EXPIRED = 3


# Number sequence statuses (finance_numbers.element_sequence_status)
NUMBER_SEQUENCE_INACTIVE = 0
NUMBER_SEQUENCE_ACTIVE = 1

# Number sequence types (finance_numbers.element_sequence_type)
NUMBER_SEQUENCE_CONTINUOUS = 1
NUMBER_SEQUENCE_NON_CONTINUOUS = 2

# Product statuses (finance_products.element_status)
PRODUCT_INACTIVE = 0
PRODUCT_ACTIVE = 1

# Product journal config statuses (finance_product_journal_config.element_status)
PRODUCT_JOURNAL_CONFIG_DRAFT = 0
PRODUCT_JOURNAL_CONFIG_APPROVED = 1
PRODUCT_JOURNAL_CONFIG_ACTIVE = 2
PRODUCT_JOURNAL_CONFIG_CLOSED = 3
