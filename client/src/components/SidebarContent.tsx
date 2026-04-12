import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function SidebarContent({ children }: CmsComponentProps): JSX.Element {
	return (
		<Box
			sx={{
				flexGrow: 1,
				overflowX: 'hidden',
				overflowY: 'auto',
				px: 0.5,
				py: 0,
			}}
		>
			{children}
		</Box>
	);
}
