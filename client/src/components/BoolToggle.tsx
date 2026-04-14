import { Box, Switch, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function BoolToggle({ node, data }: CmsComponentProps): JSX.Element {
	const value = node.fieldBinding ? Boolean(data[node.fieldBinding]) : false;

	return (
		<Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
			{node.label && (
				<Typography variant="body2" color="text.secondary">
					{node.label}
				</Typography>
			)}
			<Switch checked={value} size="small" disabled />
		</Box>
	);
}
