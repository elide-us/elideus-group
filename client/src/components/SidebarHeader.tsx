import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function SidebarHeader({ children }: CmsComponentProps): JSX.Element {
	return (
		<Box
			sx={{
				display: 'flex',
				justifyContent: 'flex-start',
				alignItems: 'center',
				pl: 1,
				py: 1,
			}}
		>
			{children}
		</Box>
	);
}
