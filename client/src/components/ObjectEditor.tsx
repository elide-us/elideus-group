import { Box, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';
import type { SelectedNode } from './Workbench';
import { COMPONENT_REGISTRY } from '../engine/registry';

export function ObjectEditor({ data, children }: CmsComponentProps): JSX.Element | null {
	if (data.__devMode !== true) {
		return null;
	}

	const selected = (data.__selectedNode as SelectedNode | null) ?? null;
	if (!selected) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="h2">Object Editor</Typography>
				<Typography variant="body2" color="text.secondary">
					Select a node in the Object Tree to edit.
				</Typography>
			</Box>
		);
	}

	if (selected.builderComponent) {
		const BuilderComponent = COMPONENT_REGISTRY[selected.builderComponent];
		if (BuilderComponent) {
			const builderProps = { data, selected } as any;
			return <BuilderComponent {...builderProps} />;
		}
	}

	return (
		<Box
			sx={{
				display: 'flex',
				flexDirection: 'column',
				height: '100%',
				width: '100%',
				p: 2,
				gap: 1,
			}}
		>
			<Typography variant="h2">{selected.categoryName}</Typography>
			<Typography variant="body2" color="text.secondary">
				Editor not available for this category yet.
			</Typography>
			{children}
		</Box>
	);
}
