import MenuIcon from '@mui/icons-material/Menu';
import { IconButton, Tooltip } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function HamburgerToggle({ data }: CmsComponentProps): JSX.Element {
	const onToggle = typeof data.__toggleSidebar === 'function' ? data.__toggleSidebar : null;

	const handleClick = (): void => {
		if (onToggle) {
			(onToggle as () => void)();
		}
	};

	return (
		<Tooltip title="Toggle Menu">
			<IconButton
				onClick={handleClick}
				sx={{
					width: 32,
					height: 32,
					color: '#FFFFFF',
					border: '1px solid #1A1A1A',
					borderRadius: 1,
					'&:hover': {
						borderColor: '#333333',
						backgroundColor: 'rgba(255, 255, 255, 0.04)',
					},
				}}
			>
				<MenuIcon sx={{ fontSize: 18 }} />
			</IconButton>
		</Tooltip>
	);
}
