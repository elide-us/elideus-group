import { Box, Typography } from '@mui/material';
import PageTitle from '../components/PageTitle';

const EmergentDevelopmentArticle = (): JSX.Element => {
	return (
		<Box sx={{ p: 2, maxWidth: 800 }}>
			<PageTitle>Emergent Development: Building Software with an AI Workforce</PageTitle>

			<Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
				March 24, 2026
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				We keep talking about AI as a coding assistant. A smarter autocomplete. A faster Stack Overflow.
				That framing undersells what is actually possible and oversells what is actually reliable. This
				article is a field report on what a real AI-assisted development workflow looks like at
				production scale &mdash; the discipline it requires, the boundaries it reveals, and the
				architectural decisions that make the difference between a system that compounds in quality and
				one that compounds in chaos.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Setting State
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				Every productive session begins the same way. Before a single feature is discussed, the
				conversation is loaded with context &mdash; the layer architecture, the RPC namespace
				conventions, the pattern compliance rules, the current version scope. This is not a courtesy.
				It is the difference between an agent that reasons within your system and one that reasons about
				a generic system that happens to share some names with yours.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				This loaded state becomes a revert point. When a feature set changes, the conversation reverts
				to this state and begins again. The conversation itself is a development artifact, treated with
				the same discipline as a branch. Drift from the established context produces drift in the
				output. The state is not assumed &mdash; it is explicitly set, every time.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Spec First
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				No code is written until the spec matches intent. The process is: describe the feature, have
				the model detail it back in full, then edit the original prompt with corrections and additional
				constraints until what the model produces matches what was actually meant. This loop continues
				until the spec is right. Only then does implementation begin.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				This step is where most of the real thinking happens. The model&rsquo;s first detailed pass
				reliably surfaces ambiguities in the original description. Edge cases appear. Layer
				responsibilities blur. The iteration is not a failure mode &mdash; it is the design process. The
				spec prompt that survives this loop is precise enough to drive implementation because it has
				been pressure-tested against a system that will immediately expose vagueness.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				The Development Cycle
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				Implementation runs through Codex, operating exclusively in the cloud. Codex builds the
				application, executes all code changes in the cloud environment, and presents a pull request.
				The agent generates the full RPC namespace as part of the build &mdash; this namespace is
				intentionally never checked into the frontend repository. It is always 100% generated at build
				time from the server-side models and dispatch definitions. The frontend never owns it. This is
				load-bearing architectural discipline, and it is worth stating plainly: the moment the generated
				namespace becomes a hand-maintained artifact, the system starts lying to itself.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				Once a PR is produced, review is mandatory and complete. Large PRs are pulled to a local branch
				for direct inspection. Smaller changes are reviewed through the Claude in Chrome MCP server
				reading the diff directly in GitHub before any commit decision is made. Nothing is assumed to be
				correct. The review is not a formality &mdash; it is where misinterpretations surface, where the
				agent&rsquo;s optimistic interpretation of an ambiguous instruction becomes visible, and where
				the prompt gets corrected before the next iteration.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				When review passes, changes are committed to the CI/CD pipeline. The pipeline performs all build
				steps again independently and runs extensive compliance, pattern, coverage, and testing systems.
				The build does not trust the review. The review does not trust the agent. Each gate is
				adversarial by design.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Tik-Tok: Features and Stability
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				Versioning follows a deliberate cadence. Odd versions introduce features. Even versions are
				stability and bug-fix releases. The current finance module &mdash; a substantial feature set
				encompassing billing imports, GL promotion, journal engines, and subledger management &mdash;
				lands in version 0.9. Version 0.10 will not add features. It will make 0.9 production-reliable.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				This pattern exists because feature work and stability work are cognitively incompatible in an
				AI-assisted context. Mixing them produces scope that exceeds what the agent can hold coherently.
				The boundary is real and it compounds with complexity &mdash; which leads to the most important
				practical discovery in this entire workflow.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				Backend and frontend changes must be separated. Not as a preference. As a hard rule. The layer
				abstraction depth in a production application &mdash; module to interface to implementation, with
				meta-abstraction layers throughout &mdash; is sufficient to exhaust the agent&rsquo;s coherent
				context before both sides of a full-stack change are complete. The agent does not fail loudly.
				It drifts. Logic migrates to the wrong layer. Assumptions about what the other side does become
				subtly wrong. Splitting the work is not a workaround. It is acknowledging the actual shape of
				the constraint.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Architectural Compliance as Adversarial Work
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				The most persistent failure mode is logic in dispatch layers. Every agent, in every session,
				will attempt to put business logic in what is supposed to be a pure routing layer. It is not
				malicious. It is the path of least resistance given the local context. The agent sees a dispatch
				function, sees that it needs to do something, and does it there.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				Left unaddressed, this proliferates. One exception becomes the pattern a future session
				references. The architecture degrades not through dramatic failures but through accumulated small
				violations that each looked reasonable in isolation.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				The response to this is structural rather than instructional. The RPC namespace is generated
				&mdash; the agent does not touch it. The dispatch layer definitions are generated from the
				database schema and server-side models at build time. The goal is to make non-compliant code
				structurally impossible rather than merely prohibited. Taking choices away from the algorithm is
				not a limitation of the workflow. It is the workflow. Every degree of freedom removed from the
				agent in a pure routing layer is a degree of freedom that cannot be misused.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				The application itself exposes an MCP server with full OAuth 2.1 compliance, giving Claude.ai
				direct read-only access to the live database &mdash; data patterns, configurations, schema, and
				the reflection tables that keep the data model consistent across layers. This means
				architectural analysis happens against the actual system state, not a description of it. Pattern
				drift is visible. Compliance gaps surface in the data, not just in the code.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				Documentation matters but is insufficient alone. The model must be explicitly instructed to read
				it. Assuming that because documentation exists it will be consulted is the kind of optimism that
				produces subtle non-compliance at scale.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Conclusion: The Discipline Is the Architecture
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				What emerges from this workflow is not an observation about AI capability. It is an observation
				about system design. The patterns that make AI-assisted development reliable &mdash; generated
				artifacts, enforced layer boundaries, adversarial review gates, explicit state management, scope
				discipline &mdash; are the same patterns that make software systems reliable in general.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				The AI does not change what good architecture looks like. It raises the cost of ignoring it.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				The agent is capable, fast, and confidently wrong in ways that compound if the system allows
				them to. The system should not allow them to. Build the environment where architectural
				violations fail to survive, and the agent becomes genuinely powerful. Build one where they
				propagate quietly, and you are managing entropy at scale.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2, fontStyle: 'italic' }}>
				The runtime is still the judge.
			</Typography>
		</Box>
	);
};

export default EmergentDevelopmentArticle;
