import { Box, Typography } from '@mui/material';

import type { PageTreeNode } from '../../api/rpc';

interface ComponentPreviewProps {
	componentName: string | null;
	componentCategory: string | null;
	treeRows: PageTreeNode[];
}

function categoryShape(category: string | null): JSX.Element {
	if (category === 'control') {
		return <Box sx={{ width: 20, height: 20, bgcolor: '#4CAF50' }} />;
	}
	if (category === 'section') {
		return <Box sx={{ width: 64, height: 34, border: '2px solid #4CAF50' }} />;
	}
	return <Box sx={{ width: 96, height: 56, border: '2px solid #4CAF50' }} />;
}

export function ComponentPreview({ componentName, componentCategory, treeRows }: ComponentPreviewProps): JSX.Element {
	void treeRows;

	return (
		<Box
			sx={{
				minHeight: 200,
				flex: 1,
				border: '1px solid #1A1A1A',
				bgcolor: '#0A0A0A',
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
				flexDirection: 'column',
				gap: 1,
			}}
		>
			<Typography variant="h6">Component Preview</Typography>
			{categoryShape(componentCategory)}
			<Typography variant="body2">{componentName ?? 'No component selected'}</Typography>
			<Typography variant="caption" sx={{ color: '#4CAF50' }}>
				{componentCategory ?? '—'}
			</Typography>
		</Box>
	);
}
