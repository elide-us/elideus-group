# Service Management

**Route:** `/service-management`

*Replaces the former ServiceRenewalsPage (`/service-renewals`). Highly abstracted — data model and workflow details are TBD.*

## Purpose

Centralized tracker for service obligations that require action — renewals, payments, expirations, and subscriptions. This is the entry point into the finance system for operational expenses and the administrative record for anything the service needs to keep alive.

## What It Tracks

- **Certificate and secret expirations** — TLS certs, signing keys, API secrets with expiry dates
- **Monthly and recurring subscriptions** — SaaS tools, cloud services, hosting
- **API key renewals** — third-party API keys with rotation schedules
- **Domain renewals** — domain registrations and their renewal windows
- **Payment requests** — outbound payments that need to be made to vendors/providers

## What It Does

- Record items with names, categories, vendors, dates (expiration, renewal-by), and costs
- Surface upcoming deadlines and overdue items
- Create payment requests that feed into the finance pipeline
- Track renewal status (upcoming, due, overdue, completed)
- Attach notes and administrative context to each item

## Relationship to Other Systems

- Creates payment requests that flow into the **finance module** for processing
- May trigger **workflow submissions** for automated renewal or payment approval flows
- Vendors referenced here connect to the **finance vendors** registry
- Categories and statuses will use standard lookup table patterns

## Description

Service obligation management page. Tracks certificates, secrets, subscriptions, API keys, domains, and payment requests with expiration dates, renewal windows, and costs. Surfaces upcoming deadlines. Creates payment requests into the finance pipeline. Data model and workflow integration details TBD.

## Seed Data

recid	element_guid	element_name	element_category	element_vendor	element_reference	element_expires_on	element_renew_by	element_renewal_cost	element_currency	element_auto_renew	element_owner	element_notes	element_status	element_created_on	element_modified_on
1	6927369A-2310-4437-8C5F-1DB606236D93	Domain Registration - elideusgroup.com	domain	name.com	elideusgroup.com	2026-05-16	2026-05-01	22.31000	USD	0	ROLE_SERVICE_ADMIN	Username/Password login aaronstackpole

Public business domain used for web presence and public email addresses.	1	2026-03-20 16:53:08.5364517 +00:00	2026-03-25 19:59:23.6928319 +00:00
4	B388604D-73A6-4C61-848C-F3BB94588472	Claude.ai Max Plan	subscription	Anthropic	claude.ai	2026-03-26	NULL	96.22000	USD	1	Aaron Stackpole	Monthly subscription ~$100/mo	1	2026-03-20 16:53:08.7948102 +00:00	2026-03-25 20:39:27.1772785 +00:00
5	9747243D-82F1-48F4-B5B9-E0ACAB4ADE0B	ChatGPT Plus	subscription	OpenAI	Apple Subscription	2026-04-24	NULL	19.99000	USD	1	Aaron Stackpole	Personal ChatGPT subscription ~$20/mo	1	2026-03-20 16:53:08.8654898 +00:00	2026-03-25 20:36:42.4314194 +00:00
6	52F21522-92BC-41C5-AE44-CD11DEB3F970	Exchange Online - Elideus Group	subscription	Microsoft	Elideus Group billing account	2026-04-17	2026-04-17	9.12000	USD	1	ROLE_SERVICE_ADMIN	2x $4 mailbox-only licenses	1	2026-03-20 16:53:08.9336651 +00:00	2026-03-25 20:02:31.1139437 +00:00
7	4CE28AEA-9C7F-447E-9AE0-959E594793B4	Domain Registration - elideus.net	domain	name.com	elideus.net	2026-05-17	2026-05-01	26.73000	USD	0	ROLE_SERVICE_ADMIN	Username/Password login aaronstackpole

Internal domain used for email (Exchange Online)	1	2026-03-25 18:47:26.2192059 +00:00	2026-03-25 19:56:28.6559085 +00:00
9	1FDD20C4-EF92-4230-A3F0-F77B2B6E56CB	TheOracleGPT - AppReg	secret	Microsoft-Azure	6c725f5b-6a44-4bf0-a0d6-c2cfc15230be	2027-03-14	2027-03-01	0.00000	USD	0	ROLE_SERVICE_ADMIN	Secret ID: 143cd2be-b820-4859-aaee-0cd7e1f241e0 "TheOracleMCP 1yr"	1	2026-03-25 20:07:41.5724330 +00:00	2026-03-25 20:07:41.5724330 +00:00
10	FBEAB24D-9574-4ABE-A488-02A7B742B135	TheOracleRPC-Billing - AppReg	secret	Microsoft-Azure	40dbfaf0-8ee1-44c1-b29c-e753c457436e	2027-03-12	2027-01-01	0.00000	USD	0	ROLE_SERVICE_ADMIN	Secret ID: 1b10bc2c-9dec-4aed-93a9-aa0a49fd027a "TheOracleRPC Billing Import 1yr"	1	2026-03-25 20:09:18.2351817 +00:00	2026-03-25 20:09:18.2351817 +00:00
11	158C6DC9-9728-4EE7-AC0F-4265E3AA9C68	Google OAuth Consent Screen (No Renewal)	secret	Google	295304659309-vkbjt5572fg3vjlqbj3qkkfgal83pcrj.apps.googleusercontent.com	NULL	NULL	0.00000	USD	0	ROLE_SERVICE_ADMIN	Project Console: https://console.cloud.google.com/iam-admin/settings?hl=en&project=theoraclerpc-auth

OAuth Settings: https://console.cloud.google.com/auth/clients?hl=en&project=theoraclerpc-auth

Google Account Login

This secret does not expire.	1	2026-03-25 20:18:56.2418114 +00:00	2026-03-25 21:07:08.2857525 +00:00
12	1A103BFF-E878-47AB-916C-2A3E0A037A43	LumaLabsAPI Key (No Renewal)	api_key	LumaLabs.ai	https://lumalabs.ai/api/keys	NULL	NULL	0.00000	USD	0	ROLE_SERVICE_ADMIN	Email/Password login aaron@elideus.net	1	2026-03-25 21:05:22.9022269 +00:00	2026-03-25 21:05:22.9022269 +00:00
13	30BE38AC-5095-4DCE-BC4A-B1D03AADBB56	OpenAI API Key (No Renewal)	api_key	OpenAI	https://platform.openai.com/settings/proj_qkVFGxwV15HylI48FEiuRS67/api-keys	NULL	NULL	0.00000	USD	0	ROLE_SERVICE_ADMIN	Apple ID Login	1	2026-03-25 21:06:32.0199698 +00:00	2026-03-25 21:06:45.8784561 +00:00