import { Box, Typography } from '@mui/material';

import { COMPONENT_REGISTRY } from './registry';
import type { PathNode } from './types';

interface WorkbenchRendererProps {
	pathData: PathNode;
	componentData: Record<string, unknown>;
}

function RenderNode({ node, data }: { node: PathNode; data: Record<string, unknown> }): JSX.Element {
	const Component = COMPONENT_REGISTRY[node.component];

	if (!Component) {
		return (
			<Box sx={{ p: 1, border: '1px dashed #333', m: 0.5 }}>
				<Typography variant="body2" color="text.secondary">
					Unknown component: {node.component}
				</Typography>
			</Box>
		);
	}

	const sortedChildren = [...node.children].sort((a, b) => a.sequence - b.sequence);
	const renderedChildren = sortedChildren.map((child) => (
		<RenderNode key={child.guid} node={child} data={data} />
	));

	return (
		<Component node={node} data={data}>
			{renderedChildren}
		</Component>
	);
}

export function WorkbenchRenderer({ pathData, componentData }: WorkbenchRendererProps): JSX.Element {
	if (pathData.component !== 'Workbench') {
		return (
			<Box sx={{ p: 4, color: 'error.main' }}>
				<Typography variant="h2">Rendering Error</Typography>
				<Typography variant="body1">
					Expected root component &quot;Workbench&quot;, received &quot;{pathData.component}&quot;.
				</Typography>
			</Box>
		);
	}

	return <RenderNode node={pathData} data={componentData} />;
}
