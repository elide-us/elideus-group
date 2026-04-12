import AccountTreeIcon from '@mui/icons-material/AccountTree';
import { Box, List, ListItemButton, ListItemIcon, ListItemText, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

const OBJECT_TREE_CATEGORIES = ['Components', 'Pages', 'Routes', 'Modules', 'Types'] as const;

export function ObjectTreeView({ data }: CmsComponentProps): JSX.Element | null {
	const isDevMode = data.__devMode === true;
	if (!isDevMode) {
		return null;
	}

	const isOpen = data.__sidebarOpen === true;

	return (
		<Box sx={{ px: 0.5, py: 0.5 }}>
			{isOpen ? (
				<Typography
					variant="body2"
					sx={{
						fontSize: '0.65rem',
						textTransform: 'uppercase',
						letterSpacing: '0.06em',
						color: '#555555',
						px: 1,
						py: 0.5,
					}}
				>
					Object Tree
				</Typography>
			) : null}
			<List sx={{ px: 0, py: 0 }}>
				{OBJECT_TREE_CATEGORIES.map((category) => (
					<ListItemButton
						key={category}
						sx={{
							minHeight: 28,
							px: '8px',
							py: '5px',
							borderRadius: 1,
							justifyContent: isOpen ? 'flex-start' : 'center',
							gap: isOpen ? 1 : 0,
							color: '#888888',
							'&:hover': {
								backgroundColor: 'rgba(255, 255, 255, 0.04)',
								color: '#FFFFFF',
							},
						}}
					>
						<ListItemIcon
							sx={{
								minWidth: 0,
								width: 18,
								height: 18,
								color: 'inherit',
								justifyContent: 'center',
								'& .MuiSvgIcon-root': { fontSize: 18 },
							}}
						>
							<AccountTreeIcon />
						</ListItemIcon>
						{isOpen ? (
							<ListItemText
								primary={category}
								primaryTypographyProps={{
									fontSize: '0.75rem',
									lineHeight: 1.2,
									whiteSpace: 'nowrap',
									overflow: 'hidden',
									textOverflow: 'ellipsis',
								}}
							/>
						) : null}
					</ListItemButton>
				))}
			</List>
		</Box>
	);
}
