import { useState } from 'react';

import { Box, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function CollapsibleSection({ node, children }: CmsComponentProps): JSX.Element {
	const [open, setOpen] = useState(true);

	return (
		<Box sx={{ mb: 1 }}>
			<Box
				onClick={() => setOpen((prev) => !prev)}
				sx={{
					cursor: 'pointer',
					bgcolor: '#0A0A0A',
					border: '1px solid #1A1A1A',
					px: 1,
					py: 0.5,
					'&:hover': { color: '#4CAF50' },
				}}
			>
				<Typography variant="subtitle2">
					{open ? '▾' : '▸'} {node.label ?? 'Section'}
				</Typography>
			</Box>
			{open && <Box sx={{ pl: 1, pt: 0.5 }}>{children}</Box>}
		</Box>
	);
}
