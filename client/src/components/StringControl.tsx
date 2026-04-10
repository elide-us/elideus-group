import { Box, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function StringControl({ node, data }: CmsComponentProps): JSX.Element {
	const value = node.fieldBinding ? data[node.fieldBinding] : null;

	return (
		<Box sx={{ mb: 1 }}>
			{node.label && (
				<Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
					{node.label}
				</Typography>
			)}
			<Typography variant="body1">{value != null ? String(value) : '—'}</Typography>
		</Box>
	);
}
