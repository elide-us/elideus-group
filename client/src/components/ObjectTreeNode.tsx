import { Box, Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function ObjectTreeNode({ node, children }: CmsComponentProps): JSX.Element {
	return (
		<Box sx={{ pl: 1 }}>
			<Typography variant="body2" sx={{ py: 0.25 }}>
				{node.label ?? node.component ?? 'Node'}
			</Typography>
			{children}
		</Box>
	);
}
