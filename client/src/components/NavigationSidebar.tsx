import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';
import { LAYOUT } from '../theme/layoutConstants';

export function NavigationSidebar({ data, children }: CmsComponentProps): JSX.Element {
	const isOpen = data.__sidebarOpen === true;

	return (
		<Box
			sx={{
				display: 'flex',
				flexDirection: 'column',
				width: isOpen ? LAYOUT.NAV_WIDTH_EXPANDED : LAYOUT.NAV_WIDTH_COLLAPSED,
				minHeight: '100vh',
				bgcolor: '#000000',
				color: '#FFFFFF',
				borderRight: '1px solid #1A1A1A',
				transition: 'width 0.2s ease',
				flexShrink: 0,
				overflow: 'hidden',
			}}
		>
			{children}
		</Box>
	);
}
