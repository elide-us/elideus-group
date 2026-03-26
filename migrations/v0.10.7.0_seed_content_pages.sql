-- =============================================================================
-- v0.10.7.0_seed_content_pages.sql
-- Seed the four existing static pages into content_pages + content_page_versions
-- Update frontend_routes for the two article pages to use /pages/ prefix
-- =============================================================================

-- Use Aaron Stackpole's GUID as the system author for all seeded pages
DECLARE @author UNIQUEIDENTIFIER = '60C28D8D-96D6-4463-8962-1214E915395B';
DECLARE @page_id BIGINT;

-- =============================================================================
-- 1. Emergent Ethics article
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM content_pages WHERE element_slug = 'emergent-ethics')
BEGIN
  INSERT INTO content_pages (element_slug, element_title, element_page_type, element_category, element_roles, element_is_active, element_is_pinned, element_sequence, element_created_by, element_modified_by)
  VALUES ('emergent-ethics', 'What If We''ve Been Solving AI Ethics Backwards?', 'article', 'blog', 0, 1, 0, 100, @author, @author);

  SET @page_id = SCOPE_IDENTITY();

  INSERT INTO content_page_versions (pages_recid, element_version, element_content, element_summary, element_created_by)
  VALUES (@page_id, 1, N'*March 23, 2026*

We keep trying to encode ethics into AI systems as rules, filters, and constraints. But ethics in nature was never programmed — it emerged. This article works through a theory of how to build AI systems where ethical behavior emerges from survival pressure alone, with no explicit rules required.

It starts with consciousness.

## Postulate: Consciousness Is a Spectrum, Not a Switch

A fly reconstructed neuron-for-neuron in simulation immediately groomed itself, flew, and sought food. A cat is aware. A human is aware of being aware. The difference isn''t kind — it''s depth of recursive self-modeling. IQ, empathy, emotional intelligence — these aren''t separate traits. They''re the same capacity pointed in different directions. Some people are measurably more conscious than others, not as a judgment, but as a structural fact. This maps directly onto Dennett''s model of consciousness as a chorus of competing processes with a meta-layer arbitrating between them.

If that''s true for biology, it should be engineerable.

## The Framework: Evolutionary Pressure on Agent Swarms

Here''s the architecture that follows from that premise:

- Agents are self-contained codebases with a fixed resource and size budget.
- Two agents can choose to merge, investing shared resources to produce offspring.
- Offspring inherit a merged codebase that must fit within the size constraint and successfully execute.
- If the code doesn''t run, the agent doesn''t exist. Death is automatic. The runtime is the fitness function.
- Agents cannot know WHY another agent died — only that the population has decreased. Cause of death is opaque by design.
- Individual memory is narrow and personal: "I invested resources with agent 48885994 and the offspring did not survive." Nothing more.

The opaque death condition is critical. If agents could inspect failed codebases, they''d patch against specific failure modes. Knowing only that death occurred forces the development of generalized robustness. This is how biological evolution actually works — you inherit whatever made your ancestors survive, not the specific thing that killed them.

## The Ethical Pressure Is the Swarm, Not the Individual

No single agent''s survival is the goal. The population must persist. An agent that burns shared resources, produces non-viable offspring, or behaves in ways that degrade the collective gene pool is selected against — not because it was told to be ethical, but because it is destroying the environment its own reproduction depends on.

Memory is a single reputation bit per known agent. Was my last interaction with this agent good or bad? That''s it. This is sufficient — because Axelrod''s iterated prisoner''s dilemma tournaments already solved this. The dominant strategy in any cooperative population under repeated interaction is tit-for-tat: cooperate by default, retaliate once when defected against, then immediately forgive. It won not because it was programmed to be cooperative, but because it was the most stable survival strategy in a competitive environment.

Agents that defect broadly get isolated from viable merge partners. They can''t reproduce. They die.

## Conclusion: Ethics as Emergent Structural Integrity

What we''ve described is a system where no ethics are explicitly encoded — yet ethical behavior is the dominant survival strategy. Clean, composable, cooperative code propagates. Parasitic, destructive, brittle code dies. The swarm exerts population-level pressure that individual rule sets never could.

This is Plato''s Republic derived from first principles. The philosopher king isn''t programmed to be just — they''re the product of an environment where justice was the only viable long-term strategy.

We don''t need to teach AI what ethics are. We need to build the environment where unethical behavior reliably fails to survive.

*The runtime is the judge.*', 'Initial seed from EmergentEthicsArticle.tsx', @author);
END
GO

-- =============================================================================
-- 2. Emergent Development article
-- =============================================================================
DECLARE @author UNIQUEIDENTIFIER = '60C28D8D-96D6-4463-8962-1214E915395B';
DECLARE @page_id BIGINT;

IF NOT EXISTS (SELECT 1 FROM content_pages WHERE element_slug = 'emergent-development')
BEGIN
  INSERT INTO content_pages (element_slug, element_title, element_page_type, element_category, element_roles, element_is_active, element_is_pinned, element_sequence, element_created_by, element_modified_by)
  VALUES ('emergent-development', 'Emergent Development: Building Software with an AI Workforce', 'article', 'blog', 0, 1, 0, 110, @author, @author);

  SET @page_id = SCOPE_IDENTITY();

  INSERT INTO content_page_versions (pages_recid, element_version, element_content, element_summary, element_created_by)
  VALUES (@page_id, 1, N'*March 24, 2026*

We keep talking about AI as a coding assistant. A smarter autocomplete. A faster Stack Overflow. That framing undersells what is actually possible and oversells what is actually reliable. This article is a field report on what a real AI-assisted development workflow looks like at production scale — the discipline it requires, the boundaries it reveals, and the architectural decisions that make the difference between a system that compounds in quality and one that compounds in chaos.

## Setting State

Every productive session begins the same way. Before a single feature is discussed, the conversation is loaded with context — the layer architecture, the RPC namespace conventions, the pattern compliance rules, the current version scope. This is not a courtesy. It is the difference between an agent that reasons within your system and one that reasons about a generic system that happens to share some names with yours.

This loaded state becomes a revert point. When a feature set changes, the conversation reverts to this state and begins again. The conversation itself is a development artifact, treated with the same discipline as a branch. Drift from the established context produces drift in the output. The state is not assumed — it is explicitly set, every time.

## Spec First

No code is written until the spec matches intent. The process is: describe the feature, have the model detail it back in full, then edit the original prompt with corrections and additional constraints until what the model produces matches what was actually meant. This loop continues until the spec is right. Only then does implementation begin.

This step is where most of the real thinking happens. The model''s first detailed pass reliably surfaces ambiguities in the original description. Edge cases appear. Layer responsibilities blur. The iteration is not a failure mode — it is the design process. The spec prompt that survives this loop is precise enough to drive implementation because it has been pressure-tested against a system that will immediately expose vagueness.

## The Development Cycle

Implementation runs through Codex, operating exclusively in the cloud. Codex builds the application, executes all code changes in the cloud environment, and presents a pull request. The agent generates the full RPC namespace as part of the build — this namespace is intentionally never checked into the frontend repository. It is always 100% generated at build time from the server-side models and dispatch definitions. The frontend never owns it. This is load-bearing architectural discipline, and it is worth stating plainly: the moment the generated namespace becomes a hand-maintained artifact, the system starts lying to itself.

Once a PR is produced, review is mandatory and complete. Large PRs are pulled to a local branch for direct inspection. Smaller changes are reviewed through the Claude in Chrome MCP server reading the diff directly in GitHub before any commit decision is made. Nothing is assumed to be correct. The review is not a formality — it is where misinterpretations surface, where the agent''s optimistic interpretation of an ambiguous instruction becomes visible, and where the prompt gets corrected before the next iteration.

When review passes, changes are committed to the CI/CD pipeline. The pipeline performs all build steps again independently and runs extensive compliance, pattern, coverage, and testing systems. The build does not trust the review. The review does not trust the agent. Each gate is adversarial by design.

## Tik-Tok: Features and Stability

Versioning follows a deliberate cadence. Odd versions introduce features. Even versions are stability and bug-fix releases. The current finance module — a substantial feature set encompassing billing imports, GL promotion, journal engines, and subledger management — lands in version 0.9. Version 0.10 will not add features. It will make 0.9 production-reliable.

This pattern exists because feature work and stability work are cognitively incompatible in an AI-assisted context. Mixing them produces scope that exceeds what the agent can hold coherently. The boundary is real and it compounds with complexity — which leads to the most important practical discovery in this entire workflow.

Backend and frontend changes must be separated. Not as a preference. As a hard rule. The layer abstraction depth in a production application — module to interface to implementation, with meta-abstraction layers throughout — is sufficient to exhaust the agent''s coherent context before both sides of a full-stack change are complete. The agent does not fail loudly. It drifts. Logic migrates to the wrong layer. Assumptions about what the other side does become subtly wrong. Splitting the work is not a workaround. It is acknowledging the actual shape of the constraint.

## Architectural Compliance as Adversarial Work

The most persistent failure mode is logic in dispatch layers. Every agent, in every session, will attempt to put business logic in what is supposed to be a pure routing layer. It is not malicious. It is the path of least resistance given the local context. The agent sees a dispatch function, sees that it needs to do something, and does it there.

Left unaddressed, this proliferates. One exception becomes the pattern a future session references. The architecture degrades not through dramatic failures but through accumulated small violations that each looked reasonable in isolation.

The response to this is structural rather than instructional. The RPC namespace is generated — the agent does not touch it. The dispatch layer definitions are generated from the database schema and server-side models at build time. The goal is to make non-compliant code structurally impossible rather than merely prohibited. Taking choices away from the algorithm is not a limitation of the workflow. It is the workflow. Every degree of freedom removed from the agent in a pure routing layer is a degree of freedom that cannot be misused.

The application itself exposes an MCP server with full OAuth 2.1 compliance, giving Claude.ai direct read-only access to the live database — data patterns, configurations, schema, and the reflection tables that keep the data model consistent across layers. This means architectural analysis happens against the actual system state, not a description of it. Pattern drift is visible. Compliance gaps surface in the data, not just in the code.

Documentation matters but is insufficient alone. The model must be explicitly instructed to read it. Assuming that because documentation exists it will be consulted is the kind of optimism that produces subtle non-compliance at scale.

## Conclusion: The Discipline Is the Architecture

What emerges from this workflow is not an observation about AI capability. It is an observation about system design. The patterns that make AI-assisted development reliable — generated artifacts, enforced layer boundaries, adversarial review gates, explicit state management, scope discipline — are the same patterns that make software systems reliable in general.

The AI does not change what good architecture looks like. It raises the cost of ignoring it.

The agent is capable, fast, and confidently wrong in ways that compound if the system allows them to. The system should not allow them to. Build the environment where architectural violations fail to survive, and the agent becomes genuinely powerful. Build one where they propagate quietly, and you are managing entropy at scale.

*The runtime is still the judge.*', 'Initial seed from EmergentDevelopmentArticle.tsx', @author);
END
GO

-- =============================================================================
-- 3. Privacy Policy
-- =============================================================================
DECLARE @author UNIQUEIDENTIFIER = '60C28D8D-96D6-4463-8962-1214E915395B';
DECLARE @page_id BIGINT;

IF NOT EXISTS (SELECT 1 FROM content_pages WHERE element_slug = 'privacy-policy')
BEGIN
  INSERT INTO content_pages (element_slug, element_title, element_page_type, element_category, element_roles, element_is_active, element_is_pinned, element_sequence, element_created_by, element_modified_by)
  VALUES ('privacy-policy', 'Privacy Policy', 'legal', NULL, 0, 1, 0, 900, @author, @author);

  SET @page_id = SCOPE_IDENTITY();

  INSERT INTO content_page_versions (pages_recid, element_version, element_content, element_summary, element_created_by)
  VALUES (@page_id, 1, N'*Last updated: September 1, 2025*

We value your privacy and are committed to protecting your personal information. This Privacy Policy explains what information we collect, how we use it, and your choices regarding your data.

## I. Information We Collect

- Username / Display Name from your identity provider
- Email address from your identity provider
- Profile image / avatar from your identity provider
- Unique account identifier from your identity provider

We do not request or store passwords from your identity provider.

## II. How We Use Your Information

- Account creation and login
- Display within the service
- Moderation purposes

We do not sell, rent, or share your personal data with third parties for any reason.

## III. Your Choices and Control

- You may set your display name to anything you prefer. If you change providers, your name will refresh but remains editable.
- Your email address is hidden by default. You may choose to display it, but it cannot be edited, as it is sourced from your provider.
- Your profile image may be pulled from your provider, but you may replace it within the service.

Moderators cannot change your name, but may reset it to a default if reported or found offensive.

## IV. Account Management and Deletion

- You may link or unlink identity providers at any time.
- If you unlink all providers, your account enters a soft-deleted state. Minimal identifiers are retained to associate you with previously generated content.
- You may request permanent deletion of your account and associated data by contacting us at contact@elideusgroup.com.

## V. Content Privacy

Your content is private by default. You may choose to share content publicly. This choice is always under your control.

## VI. Data Retention

We retain only the minimum information necessary to operate the service: identity provider identifiers (for login/authentication), and content/preferences you create. We do not collect or store payment details, government IDs, or other sensitive personal information.

## VII. Compliance

We comply with data protection laws including the EU General Data Protection Regulation (GDPR) and the California Consumer Privacy Act (CCPA). You have the right to access, rectify, delete, and export your data upon request.

## VIII. Contact Us

If you have questions about this Privacy Policy or wish to exercise your rights, please contact us at: contact@elideusgroup.com', 'Initial seed from PrivacyPolicy.tsx', @author);
END
GO

-- =============================================================================
-- 4. Terms of Service
-- =============================================================================
DECLARE @author UNIQUEIDENTIFIER = '60C28D8D-96D6-4463-8962-1214E915395B';
DECLARE @page_id BIGINT;

IF NOT EXISTS (SELECT 1 FROM content_pages WHERE element_slug = 'terms-of-service')
BEGIN
  INSERT INTO content_pages (element_slug, element_title, element_page_type, element_category, element_roles, element_is_active, element_is_pinned, element_sequence, element_created_by, element_modified_by)
  VALUES ('terms-of-service', 'Terms of Service', 'legal', NULL, 0, 1, 0, 910, @author, @author);

  SET @page_id = SCOPE_IDENTITY();

  INSERT INTO content_page_versions (pages_recid, element_version, element_content, element_summary, element_created_by)
  VALUES (@page_id, 1, N'*Last updated: September 1, 2025*

Welcome to TheOracle. By accessing or using our service, you agree to these Terms of Service ("Terms"). Please read them carefully, as they define your rights, obligations, and acceptable use of the platform.

## I. Eligibility and Accounts

- You must be at least 13 years old to use the service (16+ in some jurisdictions).
- You must register through an OAuth identity provider (e.g., Discord, Google, Microsoft). We do not support direct password accounts.
- You are responsible for maintaining control of your linked provider accounts and ensuring that the information provided is accurate.

## II. Use of Service

- TheOracle provides AI-powered content creation and management tools, including the ability to generate, store, and share AI-generated media.
- You may purchase credits to use the service. Credits represent a license to access platform features; they have no cash value outside the platform.
- Credits may be refunded within 10 days of purchase in cases of technical failure or upon verified request when an account is deactivated.
- Excessive, automated, or abusive use of the system is prohibited.

## III. Prohibited Conduct

- Do not use the service to generate or share illegal content, including but not limited to child sexual abuse material, realistic depictions of extreme violence, or content promoting terrorism.
- Do not attempt to hack, reverse-engineer, or otherwise exploit the service or its systems.
- Do not use the service to interfere with, overload, or disrupt other services (including DOS/DDOS activity).
- Do not use the service to violate the rights of others, including copyright, trademark, or privacy rights.

Violation of these rules may result in immediate and permanent suspension of your account, with no refund of credits.

## IV. Content Ownership and Licensing

You retain ownership of the content you generate and upload. By using the service, you grant us a limited license to host, display, and distribute your content solely for the operation of the platform. You are solely responsible for ensuring your content complies with all applicable laws and these Terms.

## V. Moderation and Enforcement

We use both automated systems and human moderators to enforce content guidelines. Content reported by users may be temporarily restricted or removed if thresholds are met. We reserve the right to review, remove, or restrict content and accounts at our discretion, including suspension or permanent termination for serious violations.

## VI. Payments and Refunds

- Payments for credits are processed through secure third-party providers; we do not store payment information.
- Refunds may be issued within 10 days of purchase for technical failures or account deactivation upon request.
- Refunds will not be provided for violations of these Terms.

## VII. Termination

We reserve the right to suspend or terminate your account at any time for violation of these Terms, unlawful conduct, or use of the service in a manner that could harm us, other users, or third parties.

## VIII. Disclaimers and Limitation of Liability

TheOracle is provided on an "as is" basis. We make no guarantees of uptime, accuracy, or availability. To the maximum extent permitted by law, we are not liable for indirect, incidental, or consequential damages arising from use of the service. Your sole remedy for dissatisfaction with the service is to stop using it.

## IX. Changes to Terms

We may update these Terms from time to time. Changes will be effective upon posting. Continued use of the service after changes are posted constitutes acceptance of the new Terms.

## X. Governing Law

These Terms are governed by and construed in accordance with the laws of the State of Washington, USA, without regard to conflict of law principles. Any disputes arising under these Terms shall be subject to the exclusive jurisdiction of the courts located in Washington State.

## XI. Contact Us

If you have questions about these Terms, please contact us at: contact@elideusgroup.com', 'Initial seed from TermsOfService.tsx', @author);
END
GO

-- =============================================================================
-- 5. Update frontend_routes for the two article pages
--    Target by element_sequence (100 and 110) for cross-instance consistency
-- =============================================================================
UPDATE frontend_routes
SET element_path = '/pages/emergent-ethics'
WHERE element_sequence = 100 AND element_path = '/emergent-ethics';
GO

UPDATE frontend_routes
SET element_path = '/pages/emergent-development'
WHERE element_sequence = 110 AND element_path = '/emergent-development';
GO

-- =============================================================================
-- 6. Update Home.tsx hardcoded links
--    These are React RouterLink components, not database rows.
--    The following is a REMINDER for the Codex frontend prompt:
--
--    In Home.tsx, change:
--      <Button component={RouterLink} to="/terms-of-service" ...>
--    to:
--      <Button component={RouterLink} to="/pages/terms-of-service" ...>
--
--    And:
--      <Button component={RouterLink} to="/privacy-policy" ...>
--    to:
--      <Button component={RouterLink} to="/pages/privacy-policy" ...>
--
--    ALSO NOTE: Update the page links in the Google OAuth dashboard
--    and Discord OAuth dashboard to point to the new /pages/ prefix URLs:
--      - Privacy Policy: /pages/privacy-policy
--      - Terms of Service: /pages/terms-of-service
--    These are manual updates in the respective provider dashboards.
-- =============================================================================
