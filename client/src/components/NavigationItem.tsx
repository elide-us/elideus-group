import { ListItemButton, ListItemText } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function NavigationItem({ node, data }: CmsComponentProps): JSX.Element {
	const path = node.fieldBinding ? String(data[node.fieldBinding] ?? '#') : '#';

	return (
		<ListItemButton component="a" href={path} sx={{ py: 0.5 }}>
			<ListItemText
				primary={node.label ?? 'Nav Item'}
				primaryTypographyProps={{ fontSize: '0.85rem' }}
			/>
		</ListItemButton>
	);
}
