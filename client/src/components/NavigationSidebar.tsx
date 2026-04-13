import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';
import { LAYOUT } from '../theme/layoutConstants';

export function NavigationSidebar({ data, children }: CmsComponentProps): JSX.Element {
	const isOpen = data.__sidebarOpen === true;
	const isDevMode = data.__devMode === true;
	const expandedWidth = isDevMode ? LAYOUT.NAV_WIDTH_DEV : LAYOUT.NAV_WIDTH_EXPANDED;

	return (
		<Box
			sx={{
				display: 'flex',
				flexDirection: 'column',
				width: isOpen ? expandedWidth : LAYOUT.NAV_WIDTH_COLLAPSED,
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
