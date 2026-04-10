import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function ContentPanel({ children }: CmsComponentProps): JSX.Element {
	return (
		<Box
			component="main"
			sx={{
				flex: 1,
				minWidth: 0,
				overflowY: 'auto',
				py: '14px',
				px: '18px',
			}}
		>
			{children}
		</Box>
	);
}
