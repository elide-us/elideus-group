import { Box, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';
import type { SelectedNode } from './Workbench';
import { DatabaseBuilder } from './DatabaseBuilder';
import { ModulesBuilder } from './ModulesBuilder';
import { TypesBuilder } from './TypesBuilder';

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

	if (selected.categoryName === 'database') {
		return <DatabaseBuilder data={data} selected={selected} />;
	}

	if (selected.categoryName === 'types') {
		return <TypesBuilder data={data} selected={selected} />;
	}

	if (selected.categoryName === 'modules') {
		return <ModulesBuilder data={data} selected={selected} />;
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
