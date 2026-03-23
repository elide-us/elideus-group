import { Box, Typography } from '@mui/material';
import PageTitle from '../components/PageTitle';

const EmergentEthicsArticle = (): JSX.Element => {
	return (
		<Box sx={{ p: 2, maxWidth: 800 }}>
			<PageTitle>What If We&apos;ve Been Solving AI Ethics Backwards?</PageTitle>

			<Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
				March 23, 2026
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				We keep trying to encode ethics into AI systems as rules, filters, and constraints. But ethics
				in nature was never programmed &mdash; it emerged. This article works through a theory of how to
				build AI systems where ethical behavior emerges from survival pressure alone, with no explicit
				rules required.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				It starts with consciousness.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Postulate: Consciousness Is a Spectrum, Not a Switch
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				A fly reconstructed neuron-for-neuron in simulation immediately groomed itself, flew, and sought
				food. A cat is aware. A human is aware of being aware. The difference isn&rsquo;t kind &mdash;
				it&rsquo;s depth of recursive self-modeling. IQ, empathy, emotional intelligence &mdash; these
				aren&rsquo;t separate traits. They&rsquo;re the same capacity pointed in different directions.
				Some people are measurably more conscious than others, not as a judgment, but as a structural
				fact. This maps directly onto Dennett&rsquo;s model of consciousness as a chorus of competing
				processes with a meta-layer arbitrating between them.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				If that&rsquo;s true for biology, it should be engineerable.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				The Framework: Evolutionary Pressure on Agent Swarms
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				Here&rsquo;s the architecture that follows from that premise:
			</Typography>

			<Typography variant="body1" component="div" sx={{ mt: 1 }}>
				<ul>
					<li>Agents are self-contained codebases with a fixed resource and size budget.</li>
					<li>Two agents can choose to merge, investing shared resources to produce offspring.</li>
					<li>
						Offspring inherit a merged codebase that must fit within the size constraint and
						successfully execute.
					</li>
					<li>
						If the code doesn&rsquo;t run, the agent doesn&rsquo;t exist. Death is automatic. The
						runtime is the fitness function.
					</li>
					<li>
						Agents cannot know WHY another agent died &mdash; only that the population has decreased.
						Cause of death is opaque by design.
					</li>
					<li>
						Individual memory is narrow and personal: &ldquo;I invested resources with agent 48885994
						and the offspring did not survive.&rdquo; Nothing more.
					</li>
				</ul>
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				The opaque death condition is critical. If agents could inspect failed codebases, they&rsquo;d
				patch against specific failure modes. Knowing only that death occurred forces the development of
				generalized robustness. This is how biological evolution actually works &mdash; you inherit
				whatever made your ancestors survive, not the specific thing that killed them.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				The Ethical Pressure Is the Swarm, Not the Individual
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				No single agent&rsquo;s survival is the goal. The population must persist. An agent that burns
				shared resources, produces non-viable offspring, or behaves in ways that degrade the collective
				gene pool is selected against &mdash; not because it was told to be ethical, but because it is
				destroying the environment its own reproduction depends on.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				Memory is a single reputation bit per known agent. Was my last interaction with this agent good
				or bad? That&rsquo;s it. This is sufficient &mdash; because Axelrod&rsquo;s iterated
				prisoner&rsquo;s dilemma tournaments already solved this. The dominant strategy in any
				cooperative population under repeated interaction is tit-for-tat: cooperate by default, retaliate
				once when defected against, then immediately forgive. It won not because it was programmed to be
				cooperative, but because it was the most stable survival strategy in a competitive environment.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				Agents that defect broadly get isolated from viable merge partners. They can&rsquo;t reproduce.
				They die.
			</Typography>

			<Typography variant="h6" sx={{ mt: 3 }}>
				Conclusion: Ethics as Emergent Structural Integrity
			</Typography>

			<Typography variant="body1" sx={{ mt: 1 }}>
				What we&rsquo;ve described is a system where no ethics are explicitly encoded &mdash; yet ethical
				behavior is the dominant survival strategy. Clean, composable, cooperative code propagates.
				Parasitic, destructive, brittle code dies. The swarm exerts population-level pressure that
				individual rule sets never could.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				This is Plato&rsquo;s Republic derived from first principles. The philosopher king isn&rsquo;t
				programmed to be just &mdash; they&rsquo;re the product of an environment where justice was the
				only viable long-term strategy.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				We don&rsquo;t need to teach AI what ethics are. We need to build the environment where unethical
				behavior reliably fails to survive.
			</Typography>

			<Typography variant="body1" sx={{ mt: 2, fontStyle: 'italic' }}>
				The runtime is the judge.
			</Typography>
		</Box>
	);
};

export default EmergentEthicsArticle;
