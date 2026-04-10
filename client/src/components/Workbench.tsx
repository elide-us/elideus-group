import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function Workbench({ children }: CmsComponentProps): JSX.Element {
	return (
		<Box
			sx={{
				display: 'flex',
				minHeight: '100vh',
				bgcolor: '#000000',
				color: '#FFFFFF',
			}}
		>
			{children}
		</Box>
	);
}
