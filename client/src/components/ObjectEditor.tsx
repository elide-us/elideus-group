import { Box, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function ObjectEditor({ data, children }: CmsComponentProps): JSX.Element | null {
	const isDevMode = data.__devMode === true;
	if (!isDevMode) {
		return null;
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
			<Typography variant="h2">Object Editor</Typography>
			<Typography variant="body2" color="text.secondary">
				Component Builder will render here.
			</Typography>
			{children}
		</Box>
	);
}
