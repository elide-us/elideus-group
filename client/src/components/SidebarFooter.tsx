import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function SidebarFooter({ children }: CmsComponentProps): JSX.Element {
	return (
		<Box
			sx={{
				borderTop: '1px solid #1A1A1A',
				p: 1,
			}}
		>
			{children}
		</Box>
	);
}
